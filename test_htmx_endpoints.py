#!/usr/bin/env python3
"""
HTMX Endpoint Testing Script for Productos Module
Tests all HTMX endpoints to verify they respond correctly
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
PRODUCTOS_URL = f"{BASE_URL}/productos/"

# HTMX headers to simulate real HTMX requests
HTMX_HEADERS = {
    'HX-Request': 'true',
    'HX-Trigger': 'search-input',
    'HX-Target': 'producto-table-container',
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'HTMX/1.8.4'
}

def test_endpoint(name, url, params=None, headers=None, expected_status=200):
    """Test a single endpoint and return results"""
    if headers is None:
        headers = HTMX_HEADERS
    
    try:
        start_time = time.time()
        response = requests.get(url, params=params, headers=headers)
        response_time = (time.time() - start_time) * 1000  # ms
        
        success = response.status_code == expected_status
        
        # Check if response contains expected HTMX content
        is_htmx_response = 'hx-' in response.text.lower() or 'table' in response.text.lower()
        
        return {
            'name': name,
            'url': url,
            'params': params,
            'status': response.status_code,
            'expected_status': expected_status,
            'success': success,
            'response_time_ms': round(response_time, 2),
            'content_length': len(response.text),
            'is_htmx_response': is_htmx_response,
            'error': None
        }
    except Exception as e:
        return {
            'name': name,
            'url': url,
            'params': params,
            'status': None,
            'expected_status': expected_status,
            'success': False,
            'response_time_ms': None,
            'content_length': 0,
            'is_htmx_response': False,
            'error': str(e)
        }

def run_htmx_tests():
    """Run comprehensive HTMX endpoint tests"""
    print("🚀 HTMX Productos Module Endpoint Testing")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"Test Time: {datetime.now()}")
    print()
    
    tests = [
        # Basic list view
        ("Basic List View", PRODUCTOS_URL, None),
        
        # Search tests
        ("Search by Codigo", PRODUCTOS_URL, {'search': 'VAN'}),
        ("Search by Marca", PRODUCTOS_URL, {'search': 'Nike'}),
        ("Search by Modelo", PRODUCTOS_URL, {'search': 'Comfort'}),
        ("Search by Color", PRODUCTOS_URL, {'search': 'Blanco'}),
        ("Empty Search", PRODUCTOS_URL, {'search': ''}),
        ("Special Characters", PRODUCTOS_URL, {'search': 'á-é'}),
        
        # Filter tests
        ("Filter by Temporada", PRODUCTOS_URL, {'temporada': 'Primavera'}),
        ("Filter by Oferta", PRODUCTOS_URL, {'oferta': 'true'}),
        ("Filter by Catalogo", PRODUCTOS_URL, {'catalogo': 'Principal'}),
        ("Price Min Filter", PRODUCTOS_URL, {'precio_min': '100'}),
        ("Price Max Filter", PRODUCTOS_URL, {'precio_max': '500'}),
        ("Price Range Filter", PRODUCTOS_URL, {'precio_min': '100', 'precio_max': '500'}),
        
        # Combined filters
        ("Search + Temporada", PRODUCTOS_URL, {'search': 'Nike', 'temporada': 'Verano'}),
        ("Multiple Filters", PRODUCTOS_URL, {
            'search': 'Sport', 
            'temporada': 'Verano', 
            'oferta': 'true',
            'precio_max': '300'
        }),
        
        # Pagination
        ("Pagination Page 1", PRODUCTOS_URL, {'page': '1'}),
        ("Pagination Page 2", PRODUCTOS_URL, {'page': '2'}),
        
        # Edge cases
        ("Invalid Page", PRODUCTOS_URL, {'page': '999'}),
        ("Invalid Price", PRODUCTOS_URL, {'precio_min': 'invalid'}),
        ("SQL Injection Test", PRODUCTOS_URL, {'search': "'; DROP TABLE productos; --"}),
    ]
    
    results = []
    total_tests = len(tests)
    passed_tests = 0
    
    print("📊 Running Tests...")
    print("-" * 50)
    
    for i, (name, url, params) in enumerate(tests, 1):
        print(f"[{i:2d}/{total_tests}] {name:<25}", end=" ")
        
        result = test_endpoint(name, url, params)
        results.append(result)
        
        if result['success']:
            passed_tests += 1
            status_icon = "✅"
        else:
            status_icon = "❌"
        
        print(f"{status_icon} {result['status']} ({result['response_time_ms']}ms)")
        
        if result['error']:
            print(f"        Error: {result['error']}")
    
    # Summary
    print()
    print("📈 TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print()
    
    # Performance summary
    response_times = [r['response_time_ms'] for r in results if r['response_time_ms']]
    if response_times:
        avg_response = sum(response_times) / len(response_times)
        max_response = max(response_times)
        min_response = min(response_times)
        
        print("⚡ PERFORMANCE SUMMARY")
        print("-" * 30)
        print(f"Average Response Time: {avg_response:.2f}ms")
        print(f"Fastest Response: {min_response:.2f}ms")
        print(f"Slowest Response: {max_response:.2f}ms")
        print()
    
    # Failed tests details
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        print("❌ FAILED TESTS DETAILS")
        print("-" * 30)
        for test in failed_tests:
            print(f"• {test['name']}")
            print(f"  Status: {test['status']} (expected {test['expected_status']})")
            if test['error']:
                print(f"  Error: {test['error']}")
            print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 30)
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! HTMX implementation is working correctly.")
    elif passed_tests >= total_tests * 0.9:
        print("✅ Most tests passed. Minor issues to investigate.")
    else:
        print("⚠️ Multiple test failures. Review implementation.")
    
    if response_times and avg_response > 1000:
        print("⚠️ Average response time is high. Consider optimization.")
    
    return results

if __name__ == "__main__":
    try:
        results = run_htmx_tests()
        
        # Save results to JSON file
        with open('htmx_test_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_tests': len(results),
                'passed_tests': len([r for r in results if r['success']]),
                'results': results
            }, f, indent=2)
        
        print("📁 Results saved to: htmx_test_results.json")
        
    except Exception as e:
        print(f"❌ Test runner error: {e}")
