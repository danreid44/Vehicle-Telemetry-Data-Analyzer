import sqlite3
import pandas as pd
import pytest

from analyze import (
    hex_to_rpm,
    is_pto_on,
    decode_fault,
    classify_severity,
    get_pto_stats,
    get_mtbf,
    get_fault_data,
    get_fault_stats,
)
from constants import CAN_ID_PTO, CAN_ID_FAULT


# ---------- test helper ----------

def make_telemetry_db(path, rows):
    """Build a minimal SQLite telemetry table. rows: list of (timestamp, can_id, data)."""
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE telemetry (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            can_id TEXT,
            data TEXT
        )
    """)
    conn.executemany(
        "INSERT INTO telemetry (timestamp, can_id, data) VALUES (?, ?, ?)", rows
    )
    conn.commit()
    conn.close()


# ---------- hex_to_rpm ----------

def test_hex_to_rpm_known_value():
    # 0x07D0 = 2000 raw units; at 0.125 rpm/bit that's 250 rpm
    assert hex_to_rpm("07D00000") == 250.0

def test_hex_to_rpm_zero():
    assert hex_to_rpm("00000000") == 0.0


# ---------- is_pto_on ----------

def test_is_pto_on_true_when_first_byte_is_01():
    assert is_pto_on("01AABBCC") is True

def test_is_pto_on_false_when_first_byte_is_00():
    assert is_pto_on("00AABBCC") is False


# ---------- decode_fault ----------

def test_decode_fault_valid_hex():
    # SPN 0x0064 = 100, FMI 0x00 = 0
    assert decode_fault("00640000") == (100, 0)

def test_decode_fault_too_short_returns_none_tuple():
    assert decode_fault("1234") == (None, None)

def test_decode_fault_non_hex_returns_none_tuple():
    assert decode_fault("ZZZZZZ") == (None, None)

def test_decode_fault_non_string_input_returns_none_tuple():
    assert decode_fault(None) == (None, None)


# ---------- classify_severity ----------

@pytest.mark.parametrize("fmi,expected", [
    (0, "Critical"),
    (1, "Critical"),
    (2, "Warning"),
    (3, "Warning"),
    (4, "Warning"),
    (5, "Info"),
    (31, "Info"),
])
def test_classify_severity(fmi, expected):
    assert classify_severity(fmi) == expected


# ---------- get_pto_stats: the shift/transition logic ----------

def test_get_pto_stats_counts_transitions_not_total_on_rows(tmp_path):
    db_path = tmp_path / "telemetry.db"
    # off, off, ON, ON, off, ON  -> 2 rising edges (off->on), 3 seconds spent "on"
    pattern = ["00", "00", "01", "01", "00", "01"]
    rows = [
        (f"2026-01-01T00:00:0{i}Z", CAN_ID_PTO, byte + "AABBCC")
        for i, byte in enumerate(pattern)
    ]
    make_telemetry_db(db_path, rows)

    stats = get_pto_stats(str(db_path))
    assert stats["pto_usage_count"] == 2       # engagement events, not total "on" rows
    assert stats["pto_duration_sec"] == 3

def test_get_pto_stats_all_off_has_zero_transitions(tmp_path):
    db_path = tmp_path / "telemetry.db"
    rows = [(f"2026-01-01T00:00:0{i}Z", CAN_ID_PTO, "00AABBCC") for i in range(4)]
    make_telemetry_db(db_path, rows)

    stats = get_pto_stats(str(db_path))
    assert stats["pto_usage_count"] == 0
    assert stats["pto_duration_sec"] == 0


# ---------- get_mtbf ----------

def test_get_mtbf_averages_gaps_between_timestamps():
    df = pd.DataFrame({
        "timestamp": pd.to_datetime([
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:01:00Z",  # 60s gap
            "2026-01-01T00:03:00Z",  # 120s gap
        ])
    })
    assert get_mtbf(df) == 90.0  # average of 60 and 120

def test_get_mtbf_returns_none_with_fewer_than_two_rows():
    df = pd.DataFrame({"timestamp": pd.to_datetime(["2026-01-01T00:00:00Z"])})
    assert get_mtbf(df) is None

def test_get_mtbf_returns_none_for_empty_dataframe():
    assert get_mtbf(pd.DataFrame()) is None


# ---------- get_fault_data: decode + decoder-CSV merge ----------

def test_get_fault_data_decodes_and_labels_known_fault(tmp_path):
    db_path = tmp_path / "telemetry.db"
    decoder_path = tmp_path / "decoder.csv"
    decoder_path.write_text("spn,fmi,description\n100,0,Engine Oil Pressure - Above Normal\n")

    # SPN 100 (0x0064), FMI 0 -> matches the decoder row above, and FMI 0 -> Critical
    rows = [("2026-01-01T00:00:00Z", CAN_ID_FAULT, "00640000")]
    make_telemetry_db(db_path, rows)

    df_fault = get_fault_data(str(db_path), decoder_path=str(decoder_path))
    assert len(df_fault) == 1
    assert df_fault.iloc[0]["spn"] == 100
    assert df_fault.iloc[0]["fmi"] == 0
    assert df_fault.iloc[0]["severity"] == "Critical"
    assert df_fault.iloc[0]["description"] == "Engine Oil Pressure - Above Normal"

def test_get_fault_data_unknown_spn_fmi_falls_back_to_placeholder(tmp_path):
    db_path = tmp_path / "telemetry.db"
    decoder_path = tmp_path / "decoder.csv"
    decoder_path.write_text("spn,fmi,description\n100,0,Engine Oil Pressure - Above Normal\n")

    # SPN 300 / FMI 5 has no matching row in the decoder CSV above
    rows = [("2026-01-01T00:00:00Z", CAN_ID_FAULT, "012C0500")]
    make_telemetry_db(db_path, rows)

    df_fault = get_fault_data(str(db_path), decoder_path=str(decoder_path))
    assert df_fault.iloc[0]["description"] == "Unknown SPN/FMI"


# ---------- get_fault_stats: empty vs. non-empty branch consistency ----------

def test_get_fault_stats_empty_and_nonempty_return_the_same_keys():
    empty_stats = get_fault_stats(pd.DataFrame())

    df_fault = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z"]),
        "spn": [100, 190],
        "fmi": [0, 3],
        "description": ["Oil Pressure", "Engine Speed"],
        "severity": ["Critical", "Warning"],
    })
    nonempty_stats = get_fault_stats(df_fault)

    assert set(empty_stats.keys()) == set(nonempty_stats.keys())
    assert nonempty_stats["total_faults"] == 2
    assert nonempty_stats["critical_count"] == 1
    assert nonempty_stats["warning_count"] == 1
    assert nonempty_stats["info_count"] == 0