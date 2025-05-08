# HDLF API Performance Testing Tool

This tool tests the performance of the HDLF API's WHOAMI operation by making 1000 requests and collecting statistics like average response time, 95th and 99th percentiles.

## Files Included

- `hdlf_api_perf_test.py` - The main Python script for performance testing
- `requirements.txt` - Python dependencies
- `Dockerfile` - For containerizing the application
- `config.json` - Configuration file template
- Kubernetes resources:
  - `hdlf-api-test-job.yaml` - Job definition for running the test once
  - `hdlf-api-test-configmap.yaml` - ConfigMap with configuration settings
  - `hdlf-api-certs-secret.yaml` - Secret template for storing certificates
  - `hdlf-api-test-results-pvc.yaml` - PersistentVolumeClaim for storing results
  - `hdlf-api-test-cronjob.yaml` - CronJob for scheduled testing (optional)

## Step 1: Set up your environment

Ensure you have:
- Docker installed for building the container
- Access to a Kubernetes cluster
- `kubectl` configured to access your cluster
- HDLF API client certificates

## Step 2: Configure the application

1. Edit the `config.json` file with your HDLF instance details:
   ```json
   {
     "files_rest_api": "your-hdl-instance.files.your-hdl-cluster-endpoint",
     "container": "your-container-id",
     "crt_path": "/certs/client.crt",
     "key_path": "/certs/client.key",
     "num_requests": 1000,
     "port": 443,
     "output_path": "/data/results.json"
   }
   ```

2. Update the `hdlf-api-test-configmap.yaml` with the same values.

## Step 3: Build and push the Docker image

1. Save all files to a directory on your machine
2. Navigate to that directory
3. Build the Docker image:
   ```bash
   docker build -t hdlf-api-test:latest .
   ```
4. Push to your container registry (if required):
   ```bash
   docker tag hdlf-api-test:latest your-registry/hdlf-api-test:latest
   docker push your-registry/hdlf-api-test:latest
   ```
   
   If using a private registry, update the image reference in the Kubernetes YAML files.

## Step 4: Create Kubernetes resources

1. Create the ConfigMap:
   ```bash
   kubectl apply -f hdlf-api-test-configmap.yaml
   ```

2. Create a Secret with your certificates:
   ```bash
   kubectl create secret generic hdlf-api-certs \
     --from-file=client.crt=/path/to/your/client.crt \
     --from-file=client.key=/path/to/your/client.key
   ```

3. Create the PersistentVolumeClaim for storing results:
   ```bash
   kubectl apply -f hdlf-api-test-results-pvc.yaml
   ```

4. Apply the Job or CronJob definition:
   ```bash
   # For a one-time job:
   kubectl apply -f hdlf-api-test-job.yaml
   
   # Or for scheduled testing:
   kubectl apply -f hdlf-api-test-cronjob.yaml
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

   **Option 1**: Create a pod to access the PVC data:
   ```bash
   kubectl apply -f - <<EOF
   apiVersion: v1
   kind: Pod
   metadata:
     name: results-reader
   spec:
     containers:
     - name: results-reader
       image: busybox
       command: ["sleep", "3600"]
       volumeMounts:
       - name: results-volume
         mountPath: /data
     volumes:
     - name: results-volume
       persistentVolumeClaim:
         claimName: hdlf-api-test-results-pvc
   EOF
   ```

   Then copy the results:
   ```bash
   kubectl exec results-reader -- cat /data/results.json
   # Or copy to your local machine:
   kubectl cp results-reader:/data/results.json ./results.json
   ```

   **Option 2**: Forward the results directly:
   ```bash
   kubectl exec $(kubectl get pod -l job-name=hdlf-api-test-job -o jsonpath='{.items[0].metadata.name}') -- cat /data/results.json > results.json
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

1. **Changing the number of requests**: Update the `num_requests` value in the ConfigMap or set the `NUM_REQUESTS` environment variable.

2. **Running on a schedule**: Use the CronJob definition and adjust the schedule as needed (default is daily at midnight).

3. **Saving results with timestamps**: For scheduled runs, the CronJob template automatically adds timestamps to result filenames.

4. **Running outside Kubernetes**: You can run the script directly with:
   ```bash
   python hdlf_api_perf_test.py --config /path/to/config.json
   ```

## Troubleshooting

1. **Certificate issues**: Ensure certificates are correctly formatted and have proper permissions.

2. **Connection errors**: Verify your HDLF endpoint and container values are correct.

3. **Permission issues**: The pod runs as a non-root user; ensure volumes are accessible.

4. **Results not persisting**: Check that your PVC is correctly provisioned and mounted.

## Security Notes

- The script uses client certificates for authentication
- Containers run as a non-root user for security
- Sensitive certificates are stored as Kubernetes Secrets
- Configuration can be provided via environment variables or mounted files
