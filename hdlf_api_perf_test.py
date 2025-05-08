#!/usr/bin/env python3
"""
HDLF API Performance Testing Script
Tests the HDLF API WHOAMI operation and collects performance statistics
"""

import http.client
import ssl
import time
import json
import os
import numpy as np
import argparse
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hdlf-api-test")

def load_config():
    """Load configuration from environment variables or config file"""
    config = {
        'files_rest_api': os.environ.get('FILES_REST_API'),
        'container': os.environ.get('CONTAINER'),
        'crt_path': os.environ.get('CRT_PATH'),
        'key_path': os.environ.get('KEY_PATH'),
        'num_requests': int(os.environ.get('NUM_REQUESTS', '1000')),
        'port': int(os.environ.get('API_PORT', '443')),
        'output_path': os.environ.get('OUTPUT_PATH', '/data/results.json'),
        'debug': os.environ.get('DEBUG', 'false').lower() in ('true', 'yes', '1')
    }
    
    # Check if config file exists and load from it if environment vars not set
    config_file = os.environ.get('CONFIG_FILE', '/config/config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                # Only override values that are not already set from env vars
                for key, value in file_config.items():
                    if config.get(key) is None:
                        config[key] = value
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
    
    # Validate required config values
    required_keys = ['files_rest_api', 'container', 'crt_path', 'key_path']
    missing_keys = [key for key in required_keys if not config.get(key)]
    if missing_keys:
        raise ValueError(f"Missing required configuration: {', '.join(missing_keys)}")
    
    # Add timestamp to output_path if it doesn't already have one
    if 'output_path' in config and not '%' in config['output_path']:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base, ext = os.path.splitext(config['output_path'])
        config['output_path'] = f"{base}_{timestamp}{ext}"
        logger.info(f"Added timestamp to output path: {config['output_path']}")
    
    # Set logging level based on debug mode
    if config.get('debug', False):
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    return config

def create_ssl_context(config):
    """Create SSL context with client certificates"""
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.load_cert_chain(certfile=config['crt_path'], keyfile=config['key_path'])
        return context
    except Exception as e:
        logger.error(f"Error creating SSL context: {e}")
        raise

def whoami_request(config, ssl_context):
    """Make a single WHOAMI request and return the response time"""
    start_time = time.time()
    success = False
    response_body = None
    status_code = None
    
    try:
        request_url = '/webhdfs/v1/?op=WHOAMI'
        request_headers = {
            'x-sap-filecontainer': config['container'],
            'Content-Type': 'application/json'
        }
        
        connection = http.client.HTTPSConnection(
            config['files_rest_api'], 
            port=config['port'],
            context=ssl_context
        )
        
        connection.request(
            method="GET",
            url=request_url,
            body=None,
            headers=request_headers
        )
        
        response = connection.getresponse()
        status_code = response.status
        response_body = response.read().decode()
        
        if 200 <= status_code < 300:
            success = True
        
        # Print debug information if debug mode is enabled
        if config.get('debug', False):
            logger.debug(f"Request URL: {request_url}")
            logger.debug(f"Headers: {request_headers}")
            logger.debug(f"Status Code: {status_code}")
            logger.debug(f"Response Body: {response_body}")
        
        response.close()
    except Exception as e:
        logger.error(f"Request error: {e}")
        if config.get('debug', False):
            logger.exception("Detailed error information:")
    finally:
        end_time = time.time()
        duration = (end_time - start_time) * 1000  # Convert to milliseconds
        
    return {
        'duration_ms': duration,
        'success': success,
        'status_code': status_code,
        'response': response_body
    }

def run_batch_test(config):
    """Run a batch of WHOAMI requests and collect statistics"""
    logger.info(f"Starting batch test of {config['num_requests']} WHOAMI requests")
    
    ssl_context = create_ssl_context(config)
    results = []
    successful_requests = 0
    
    test_start_time = time.time()
    
    for i in range(config['num_requests']):
        if i % 100 == 0 and i > 0:
            logger.info(f"Completed {i} requests...")
            
        result = whoami_request(config, ssl_context)
        results.append(result)
        
        if result['success']:
            successful_requests += 1
        elif config.get('debug', False):
            logger.debug(f"Request {i+1} failed with status code {result['status_code']}")
            
    test_end_time = time.time()
    total_test_duration = test_end_time - test_start_time
    
    # In debug mode, log summary of failed requests
    if config.get('debug', False):
        failed_requests = [r for r in results if not r['success']]
        if failed_requests:
            logger.debug(f"Total failed requests: {len(failed_requests)}")
            for i, req in enumerate(failed_requests[:5]):  # Show first 5 failed requests
                logger.debug(f"Failed request {i+1}: Status code: {req['status_code']}, Response: {req['response'][:200]}...")
            if len(failed_requests) > 5:
                logger.debug(f"... and {len(failed_requests) - 5} more failures")
    
    return {
        'results': results,
        'successful_requests': successful_requests,
        'total_test_duration': total_test_duration
    }

def calculate_statistics(test_results):
    """Calculate statistics from test results"""
    durations = [r['duration_ms'] for r in test_results['results'] if r['success']]
    
    if not durations:
        logger.error("No successful requests to calculate statistics from!")
        return {
            'success_rate': 0,
            'total_requests': len(test_results['results']),
            'successful_requests': 0
        }
    
    # Calculate statistics using numpy
    mean = np.mean(durations)
    median = np.median(durations)
    std_dev = np.std(durations)
    percentile_95 = np.percentile(durations, 95)
    percentile_99 = np.percentile(durations, 99)
    min_duration = np.min(durations)
    max_duration = np.max(durations)
    
    # Calculate requests per second
    total_time = test_results['total_test_duration']
    requests_per_second = len(test_results['results']) / total_time if total_time > 0 else 0
    
    success_rate = (test_results['successful_requests'] / len(test_results['results'])) * 100
    
    return {
        'mean_ms': mean,
        'median_ms': median,
        'std_dev_ms': std_dev,
        'percentile_95_ms': percentile_95,
        'percentile_99_ms': percentile_99,
        'min_ms': min_duration,
        'max_ms': max_duration,
        'requests_per_second': requests_per_second,
        'success_rate': success_rate,
        'total_requests': len(test_results['results']),
        'successful_requests': test_results['successful_requests'],
        'total_duration_seconds': test_results['total_test_duration']
    }

def save_results(statistics, config):
    """Save test results to a file"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    output_data = {
        'test_time': timestamp,
        'config': {
            'files_rest_api': config['files_rest_api'],
            'container': config['container'],
            'num_requests': config['num_requests']
        },
        'statistics': statistics
    }
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(config['output_path']), exist_ok=True)
    
    with open(config['output_path'], 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Results saved to {config['output_path']}")

def display_results(statistics):
    """Display test results in a readable format"""
    logger.info("\n" + "="*50)
    logger.info("HDLF API WHOAMI PERFORMANCE TEST RESULTS")
    logger.info("="*50)
    logger.info(f"Total Requests: {statistics['total_requests']}")
    logger.info(f"Successful Requests: {statistics['successful_requests']}")
    logger.info(f"Success Rate: {statistics['success_rate']:.2f}%")
    logger.info(f"Total Test Duration: {statistics['total_duration_seconds']:.2f} seconds")
    logger.info(f"Requests Per Second: {statistics['requests_per_second']:.2f}")
    logger.info("\nResponse Time Statistics (milliseconds):")
    logger.info(f"Mean: {statistics['mean_ms']:.2f} ms")
    logger.info(f"Median: {statistics['median_ms']:.2f} ms")
    logger.info(f"Standard Deviation: {statistics['std_dev_ms']:.2f} ms")
    logger.info(f"95th Percentile: {statistics['percentile_95_ms']:.2f} ms")
    logger.info(f"99th Percentile: {statistics['percentile_99_ms']:.2f} ms")
    logger.info(f"Min: {statistics['min_ms']:.2f} ms")
    logger.info(f"Max: {statistics['max_ms']:.2f} ms")
    logger.info("="*50)

def main():
    """Main function to run the API performance test"""
    parser = argparse.ArgumentParser(description='HDLF API Performance Testing')
    parser.add_argument('--config', help='Path to config file')
    args = parser.parse_args()
    
    if args.config:
        os.environ['CONFIG_FILE'] = args.config
    
    try:
        logger.info("Loading configuration...")
        config = load_config()
        
        logger.info(f"Starting API test against {config['files_rest_api']} for {config['num_requests']} requests")
        test_results = run_batch_test(config)
        
        logger.info("Calculating statistics...")
        statistics = calculate_statistics(test_results)
        
        display_results(statistics)
        save_results(statistics, config)
        
        logger.info("Test completed successfully")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
