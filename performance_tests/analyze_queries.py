"""
Query analysis script for Pronto Shoes POS.
This script profiles slow database queries and identifies optimization opportunities.
"""
import os
import sys
import time
import logging
import statistics
from collections import defaultdict

# Add project to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pronto_shoes.settings")

import django
django.setup()

from django.db import connection, reset_queries
from django.conf import settings
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("performance_tests/query_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure DEBUG is set to True to capture queries
settings.DEBUG = True


def authenticate_client():
    """Authenticate and return a client with valid token."""
    client = APIClient()
    # You would need a valid user in the system for this to work
    client.login(username="admin", password="admin")
    return client


def measure_endpoint_performance(client, endpoint, method="get", data=None, repeat=10):
    """Measure performance of a specific endpoint with detailed query analysis."""
    logger.info(f"Testing endpoint: {endpoint}")
    
    query_counts = []
    response_times = []
    query_details = defaultdict(list)
    
    for i in range(repeat):
        # Clear the query log before each request
        reset_queries()
        
        # Measure performance with query capture
        with CaptureQueriesContext(connection) as context:
            start_time = time.time()
            
            if method.lower() == "get":
                response = client.get(endpoint)
            elif method.lower() == "post":
                response = client.post(endpoint, data=data)
            elif method.lower() == "put":
                response = client.put(endpoint, data=data)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return
                
            end_time = time.time()
        
        # Record statistics
        duration = end_time - start_time
        query_count = len(context.captured_queries)
        
        query_counts.append(query_count)
        response_times.append(duration)
        
        # Analyze individual queries
        for query in context.captured_queries:
            sql = query["sql"]
            query_time = float(query["time"])
            query_details[sql].append(query_time)
        
        # Add a small delay between requests
        time.sleep(0.1)
    
    # Calculate and log metrics
    avg_response_time = statistics.mean(response_times)
    avg_query_count = statistics.mean(query_counts)
    status_code = response.status_code
    
    logger.info(f"Endpoint: {endpoint} (Method: {method})")
    logger.info(f"Status Code: {status_code}")
    logger.info(f"Average Response Time: {avg_response_time:.4f} seconds")
    logger.info(f"Average Query Count: {avg_query_count:.1f}")
    
    # Identify slow queries
    logger.info("Analyzing slow queries:")
    
    # Sort queries by average execution time
    sorted_queries = sorted(
        query_details.items(),
        key=lambda x: statistics.mean(x[1]),
        reverse=True
    )
    
    # Log the top 5 slowest queries
    for i, (sql, times) in enumerate(sorted_queries[:5], 1):
        avg_time = statistics.mean(times)
        frequency = len(times)
        logger.info(f"Slow Query #{i}:")
        logger.info(f"  Avg Time: {avg_time:.4f} seconds")
        logger.info(f"  Frequency: {frequency}/{repeat} requests")
        logger.info(f"  SQL: {sql[:200]}...")  # Truncate long queries
        logger.info("---")
    
    return {
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "avg_response_time": avg_response_time,
        "avg_query_count": avg_query_count,
        "slowest_query_time": statistics.mean(sorted_queries[0][1]) if sorted_queries else 0
    }


def main():
    """Run performance analysis on critical endpoints."""
    logger.info("Starting database query analysis")
    client = authenticate_client()
    results = []
    
    # Test critical endpoints
    endpoints = [
        # List endpoints
        {"endpoint": "/api/productos/", "method": "get"},
        {"endpoint": "/api/clientes/", "method": "get"},
        {"endpoint": "/api/pedidos/", "method": "get"},
        {"endpoint": "/api/inventario/", "method": "get"},
        
        # Detail endpoints
        {"endpoint": "/api/productos/1/", "method": "get"},
        {"endpoint": "/api/clientes/1/", "method": "get"},
        
        # Report endpoints (likely to be query-intensive)
        {"endpoint": "/api/reportes/pedidos_por_surtir/", "method": "get"},
        {"endpoint": "/api/reportes/apartados_por_cliente/", "method": "get"}
    ]
    
    for endpoint_info in endpoints:
        result = measure_endpoint_performance(client, **endpoint_info)
        results.append(result)
    
    # Sort and display summary by response time
    logger.info("\nPERFORMANCE SUMMARY (sorted by response time):")
    sorted_results = sorted(results, key=lambda x: x["avg_response_time"], reverse=True)
    
    for i, result in enumerate(sorted_results, 1):
        logger.info(f"{i}. {result['endpoint']} ({result['method']}): " +
                   f"{result['avg_response_time']:.4f}s, " +
                   f"{result['avg_query_count']:.1f} queries, " +
                   f"Status: {result['status_code']}")
    
    logger.info("\nOptimization Recommendations:")
    for result in sorted_results[:3]:  # Focus on the 3 slowest endpoints
        logger.info(f"Endpoint {result['endpoint']} - Recommendations:")
        
        if result["avg_query_count"] > 10:
            logger.info("  - High query count: Consider using select_related/prefetch_related")
            
        if result["slowest_query_time"] > 0.1:
            logger.info("  - Slow queries detected: Review indexes and query optimization")
            
        if result["avg_response_time"] > 0.5:
            logger.info("  - Response time exceeds 500ms: Consider caching or query optimization")
    
    logger.info("Query analysis complete")


if __name__ == "__main__":
    main() 