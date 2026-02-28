FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Ensure the backend points to the internal Docker models directory
ENV TIRE_MODEL_DIR=/app/models

# Install dependencies
COPY requirements.txt .
# Exclude torch CPU overhead in slim environments if desired, but here we just install the standard reqs
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
# Copy models directory (make sure it contains the .pt and .meta.json)
COPY models/ ./models/

# Expose the API port
EXPOSE 8000

# Run uvicorn server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
