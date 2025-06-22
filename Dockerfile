FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY hdlf_api_perf_test.py .

# Set execute permissions
RUN chmod +x hdlf_api_perf_test.py

# Create directories for mounting volumes
RUN mkdir -p /config /data /certs

# Set environment variables with defaults to be overridden at runtime
ENV FILES_REST_API=""
ENV CONTAINER=""
ENV CRT_PATH="/certs/tls.crt"
ENV KEY_PATH="/certs/tls.key"
ENV NUM_REQUESTS="1000"
ENV CONFIG_FILE="/config/config.json"
ENV OUTPUT_PATH="/data/results.json"

# Run as non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app /config /data /certs
USER appuser

# Command to run the application
ENTRYPOINT ["python", "hdlf_api_perf_test.py"]