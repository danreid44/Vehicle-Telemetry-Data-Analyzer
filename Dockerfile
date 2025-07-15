# Use official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Default command runs dashboard
CMD ["streamlit", "run", "dashboard.py"]
