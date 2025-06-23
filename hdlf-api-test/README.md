# HDLF API Performance Test Helm Chart

This Helm chart deploys the HDLF API Performance Testing tool, which tests the performance of the HDLF API's WHOAMI operation by making requests and collecting statistics like average response time, 95th and 99th percentiles.

## Prerequisites

- Kubernetes 1.16+
- Helm 3.0+
- Access to a Kubernetes cluster
- HDLF API client certificates (if not using the certificate resource)

## Installing the Chart

To install the chart with the release name `hdlf-test`:

```bash
# Using default values
helm install hdlf-test ./hdlf-api-test

# Using custom values file
helm install hdlf-test ./hdlf-api-test -f values-custom.yaml

# Using specific landscape values
helm install hdlf-test ./hdlf-api-test -f values-eu10.yaml
```

## Uninstalling the Chart

To uninstall/delete the `hdlf-test` deployment:

```bash
helm delete hdlf-test
```

## Configuration

The following table lists the configurable parameters of the HDLF API Performance Test chart and their default values.

| Parameter | Description | Default |
| --------- | ----------- | ------- |
| `image.repository` | Image repository | `sfroee/hdlf-api-test` |
| `image.tag` | Image tag | `latest` |
| `image.digest` | Image digest (recommended for production) | `sha256:b369ffc566e381363a889c4c049ba824406636fdcf4b7d7db11c44d545f7783a` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `hdlf.filesRestApi` | HDLF instance endpoint | `your-hdl-instance.files.your-hdl-cluster-endpoint` |
| `hdlf.container` | Container ID | `your-container-id` |
| `hdlf.numRequests` | Number of requests to make | `1000` |
| `hdlf.debug` | Debug mode | `false` |
| `hdlf.port` | API port | `443` |
| `hdlf.outputPath` | Output path for results | `/data/results.json` |
| `hdlf.certPath` | Certificate path | `/certs/client.crt` |
| `hdlf.keyPath` | Key path | `/certs/client.key` |
| `certificate.create` | Whether to create a Certificate resource | `false` |
| `certificate.subject` | Subject for the certificate | `CN=hdlf-api-test,O=SAP SE,C=DE` |
| `certificate.issuerRef.group` | Certificate issuer group | `btp-certificate-issuer.btp.sap.com` |
| `certificate.issuerRef.kind` | Certificate issuer kind | `Issuer` |
| `certificate.issuerRef.name` | Certificate issuer name | `btp-cert-svc-issuer` |
| `secret.create` | Whether to create a Secret resource | `false` |
| `secret.clientCrt` | Base64-encoded client certificate | `""` |
| `secret.clientKey` | Base64-encoded client key | `""` |
| `persistence.size` | Size of the PVC | `50Mi` |
| `persistence.storageClassName` | Storage class name | `default` |
| `persistence.accessModes` | Access modes | `[ReadWriteOnce]` |
| `job.create` | Whether to create a Job resource | `true` |
| `job.createDebug` | Whether to create a debug Job resource | `false` |
| `job.ttlSecondsAfterFinished` | TTL seconds after finished | `86400` |
| `job.backoffLimit` | Backoff limit | `3` |
| `job.resources.requests.cpu` | CPU requests | `500m` |
| `job.resources.requests.memory` | Memory requests | `256Mi` |
| `job.resources.limits.cpu` | CPU limits | `1` |
| `job.resources.limits.memory` | Memory limits | `512Mi` |
| `cronjob.create` | Whether to create a CronJob resource | `false` |
| `cronjob.schedule` | Schedule for the CronJob | `@every 57m` |
| `cronjob.concurrencyPolicy` | Concurrency policy | `Forbid` |
| `cronjob.successfulJobsHistoryLimit` | Successful jobs history limit | `2` |
| `cronjob.failedJobsHistoryLimit` | Failed jobs history limit | `3` |
| `resultExtractionPod.create` | Whether to create a result extraction Pod resource | `false` |
| `resultExtractionPod.timeToLive` | Time to live in seconds | `3600` |
| `securityContext.runAsNonRoot` | Run as non-root | `true` |
| `securityContext.runAsUser` | Run as user | `1000` |
| `securityContext.runAsGroup` | Run as group | `1000` |
| `securityContext.fsGroup` | FS group | `1000` |
| `securityContext.container.allowPrivilegeEscalation` | Allow privilege escalation | `false` |
| `securityContext.container.capabilities.drop` | Drop capabilities | `[ALL]` |

## Landscape-specific Configuration

The chart includes example values files for different landscapes:

- `values-eu10.yaml`: Configuration for EU10 landscape
- `values-us30.yaml`: Configuration for US30 landscape with certificate creation

You can create your own values files for other landscapes by copying and modifying these examples.

## Certificate Management

The chart supports three methods for managing certificates:

1. **Using the Certificate resource**: Set `certificate.create=true` to create a Certificate resource that uses the BTP certificate issuer to generate client certificates.

2. **Using an existing Secret**: If you already have a Secret with client certificates, you can use it directly. The Secret should have `client.crt` and `client.key` keys.

3. **Creating a Secret with values**: Set `secret.create=true` and provide base64-encoded certificates in `secret.clientCrt` and `secret.clientKey`.

## Usage Examples

### Running a one-time test

```bash
helm install hdlf-test ./hdlf-api-test \
  --set hdlf.filesRestApi=your-hdl-instance.files.your-hdl-cluster-endpoint \
  --set hdlf.container=your-container-id \
  --set job.create=true
```

### Running a debug test

```bash
helm install hdlf-test ./hdlf-api-test \
  --set hdlf.filesRestApi=your-hdl-instance.files.your-hdl-cluster-endpoint \
  --set hdlf.container=your-container-id \
  --set job.createDebug=true
```

### Setting up a scheduled test

```bash
helm install hdlf-test ./hdlf-api-test \
  --set hdlf.filesRestApi=your-hdl-instance.files.your-hdl-cluster-endpoint \
  --set hdlf.container=your-container-id \
  --set cronjob.create=true \
  --set cronjob.schedule="0 0 * * *"
```

### Using certificates from a Secret

```bash
# First create the secret with your certificates
kubectl create secret generic hdlf-api-certs \
  --from-file=client.crt=/path/to/your/client.crt \
  --from-file=client.key=/path/to/your/client.key

# Then install the chart
helm install hdlf-test ./hdlf-api-test \
  --set hdlf.filesRestApi=your-hdl-instance.files.your-hdl-cluster-endpoint \
  --set hdlf.container=your-container-id
```

### Creating certificates with the BTP certificate issuer

```bash
helm install hdlf-test ./hdlf-api-test \
  --set hdlf.filesRestApi=your-hdl-instance.files.your-hdl-cluster-endpoint \
  --set hdlf.container=your-container-id \
  --set certificate.create=true \
  --set certificate.subject="CN=hdlf-api-test,O=SAP SE,C=DE"
```

## Accessing Test Results

The test results are stored in a PersistentVolumeClaim. To access them, you can create a result extraction pod:

```bash
helm install hdlf-test ./hdlf-api-test \
  --set hdlf.filesRestApi=your-hdl-instance.files.your-hdl-cluster-endpoint \
  --set hdlf.container=your-container-id \
  --set resultExtractionPod.create=true
```

Then copy the results:

```bash
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
