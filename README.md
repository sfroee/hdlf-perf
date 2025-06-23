# HDLF API Performance Testing Tool

This tool tests the performance of the HDLF API's WHOAMI operation by making requests and collecting statistics like average response time, 95th and 99th percentiles.

## Files Included

- `hdlf_api_perf_test.py` - The main Python script for performance testing
- `requirements.txt` - Python dependencies (numpy)
- `Dockerfile` - For containerizing the application
- Kubernetes resources:
  - `k8s_hdlf-api-test-job.yaml` - Job definition for running the full test
  - `k8s_hdlf-api-test-job-debug.yaml` - Debug Job with smaller batch size for testing
  - `k8s_configmap.yaml` - ConfigMap with configuration settings
  - `k8s_secret.yaml` - Secret template for storing certificates
  - `k8s_pvc.yaml` - PersistentVolumeClaim for storing results
  - `k8s_cronjob.yaml` - CronJob for scheduled testing (optional)
  - `result_extraction_pod.yaml` - Pod for accessing test results
- Helm chart:
  - `hdlf-api-test/` - Helm chart for easy deployment and configuration

## Installation Options

You can deploy this tool using either the raw Kubernetes manifests or the Helm chart.

### Option 1: Using Helm Chart (Recommended)

The Helm chart provides an easy way to deploy and configure the HDLF API Performance Testing tool with a single command.

```bash
# Install with default values
helm install hdlf-test ./hdlf-api-test

# Install with landscape-specific values
helm install hdlf-test ./hdlf-api-test -f hdlf-api-test/values-eu10.yaml

# Install with custom values
helm install hdlf-test ./hdlf-api-test --set hdlf.filesRestApi=your-hdl-instance.files.your-hdl-cluster-endpoint --set hdlf.container=your-container-id
```

For detailed information about the Helm chart, see the [Helm Chart README](./hdlf-api-test/README.md).

### Option 2: Using Kubernetes Manifests Directly

Follow the steps below to deploy using the raw Kubernetes manifests.

## Step 1: Set up your environment

Ensure you have:
- Docker installed for building the container
- Access to a Kubernetes cluster
- `kubectl` configured to access your cluster
- HDLF API client certificates

## Step 2: Configure the application

1. Edit the `k8s_configmap.yaml` file with your HDLF instance details:
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: hdlf-api-test-config
   data:
     files_rest_api: "your-hdl-instance.files.your-hdl-cluster-endpoint"
     container: "your-container-id"
     num_requests: "1000"
     debug: "false"
     config.json: |
       {
         "files_rest_api": "your-hdl-instance.files.your-hdl-cluster-endpoint",
         "container": "your-container-id",
         "crt_path": "/certs/tls.crt",
         "key_path": "/certs/tls.key",
         "num_requests": 1000,
         "port": 443,
         "output_path": "/data/results.json",
         "debug": false
       }
   ```

## Step 3: Build and push the Docker image

1. Save all files to a directory on your machine
2. Navigate to that directory
3. Build the Docker image:
   ```bash
   docker build --platform linux/amd64 -t hdlf-api-test:latest .
   ```
4. Push to your container registry:
   ```bash
   docker tag hdlf-api-test:latest your-registry/hdlf-api-test:latest
   docker push your-registry/hdlf-api-test:latest
   ```
   
   Note: The default K8s manifests use the image `sfroee/hdlf-api-test@sha256:2e16baf7f3c56988f3f607a6f5902c11bcb3b3a1f892114ff9398117c8d227c4`. If you push to your own registry, remember to update the image reference in the Kubernetes YAML files.

## Step 4: Create Kubernetes resources

1. Create the ConfigMap:
   ```bash
   kubectl apply -f k8s_configmap.yaml
   ```

2. Create a Secret with your certificates - you have two options:

   **Option A**: Using kubectl create command:
   ```bash
   kubectl create secret generic hdlf-api-certs \
     --from-file=tls.crt=/path/to/your/client.crt \
     --from-file=tls.key=/path/to/your/client.key
   ```
   
   **Option B**: Edit the k8s_secret.yaml file directly with base64-encoded certificates:
   ```bash
   # First, encode your certificates to base64
   cat /path/to/your/client.crt | base64 -w 0 > client.crt.b64
   cat /path/to/your/client.key | base64 -w 0 > client.key.b64
   
   # Then edit k8s_secret.yaml to replace the placeholders with your actual encoded certificates
   # Replace <BASE64_ENCODED_CLIENT_CRT> with the content of client.crt.b64
   # Replace <BASE64_ENCODED_CLIENT_KEY> with the content of client.key.b64
   
   # Finally, apply the secret
   kubectl apply -f k8s_secret.yaml
   ```

3. Create the PersistentVolumeClaim for storing results:
   ```bash
   kubectl apply -f k8s_pvc.yaml
   ```

4. Apply the Job or CronJob definition:
   ```bash
   # For a one-time job:
   kubectl apply -f k8s_hdlf-api-test-job.yaml
   
   # For debug mode with fewer requests (10):
   kubectl apply -f k8s_hdlf-api-test-job-debug.yaml
   
   # Or for scheduled testing:
   kubectl apply -f k8s_cronjob.yaml
   ```

## Step 5: Run the test and view results

1. Check the status of the job:
   ```bash
   kubectl get jobs
   kubectl get pods  # See the pod created by the job
   ```

2. Monitor the job's progress:
   ```bash
   kubectl logs -f job/hdlf-api-test-job
   ```

3. Once complete, you can access the results by:

   Create a pod to access the PVC data:
   ```bash
   kubectl apply -f result_extraction_pod.yaml
   ```

   Then copy the results:
   ```bash
   kubectl exec results-reader -- ls /data/
   kubectl cp results-reader:/data/ ./results/
   ```

## Understanding the Results

The output JSON file contains:

```json
{
  "test_time": "2025-05-08_14-30-00",
  "config": {
    "files_rest_api": "your-hdl-instance.files.your-hdl-cluster-endpoint",
    "container": "your-container-id",
    "num_requests": 1000
  },
  "statistics": {
    "mean_ms": 123.45,
    "median_ms": 115.67,
    "std_dev_ms": 25.89,
    "percentile_95_ms": 175.32,
    "percentile_99_ms": 210.45,
    "min_ms": 95.12,
    "max_ms": 345.67,
    "requests_per_second": 8.76,
    "success_rate": 99.8,
    "total_requests": 1000,
    "successful_requests": 998,
    "total_duration_seconds": 114.23
  }
}
```

Key statistics include:
- `mean_ms`: Average response time in milliseconds
- `median_ms`: Median response time
- `percentile_95_ms` and `percentile_99_ms`: 95th and 99th percentile response times
- `requests_per_second`: Overall throughput
- `success_rate`: Percentage of successful requests

## Customization Options

1. **Changing the number of requests**: 
   - Update the `num_requests` value in the ConfigMap
   - Set the `NUM_REQUESTS` environment variable in the job YAML
   - Use the debug job for a smaller batch of requests (10)

2. **Running on a schedule**: Use the CronJob definition and adjust the schedule as needed (default is every 57 minutes).

3. **Saving results with timestamps**: The script automatically adds timestamps to result filenames if they don't already have one.

4. **Running outside Kubernetes**: You can run the script directly with:
   ```bash
   python hdlf_api_perf_test.py --config /path/to/config.json
   ```

5. **Running in debug mode**: 
   - Set the `debug` value to "true" in the ConfigMap
   - Use the dedicated debug job (`k8s_hdlf-api-test-job-debug.yaml`) which limits to 10 requests and enables debug mode

## Environment Variables

The application supports the following environment variables:

- `FILES_REST_API`: The HDLF API endpoint
- `CONTAINER`: The container ID
- `CRT_PATH`: Path to client certificate (default: "/certs/client.crt")
- `KEY_PATH`: Path to client key (default: "/certs/client.key")
- `NUM_REQUESTS`: Number of requests to make (default: "1000")
- `API_PORT`: API port number (default: "443")
- `OUTPUT_PATH`: Path to save results (default: "/data/results.json")
- `DEBUG`: Enable debug mode (default: "false")
- `CONFIG_FILE`: Path to config file (default: "/config/config.json")

## Troubleshooting

1. **Certificate issues**: Ensure certificates are correctly formatted and have proper permissions.

2. **Connection errors**: Verify your HDLF endpoint and container values are correct.

3. **Permission issues**: The pod runs as a non-root user; ensure volumes are accessible.

4. **Results not persisting**: Check that your PVC is correctly provisioned and mounted.

5. **Debug mode**: Enable debug mode for more detailed logs about requests and responses.

## Security Notes

- The script uses client certificates for authentication
- Containers run as a non-root user (1000) for security
- Sensitive certificates are stored as Kubernetes Secrets
- Container capabilities are dropped for enhanced security
- Configuration can be provided via environment variables or mounted files
