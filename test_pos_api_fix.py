#!/usr/bin/env python
"""
Test script to verify the POS API fix is working correctly.
This script simulates the frontend API call with the corrected data structure.
"""

import requests
import json
from datetime import date

# Test data matching the corrected frontend structure
test_data = {
    "fecha": date.today().isoformat(),  # YYYY-MM-DD format
    "tipo": "venta",
    "tienda": 1,  # Assuming tienda ID 1 exists
    "pagado": True,  # Sale is paid
    "detalles": [
        {
            "producto": 1,  # Assuming producto ID 1 exists
            "cantidad": 2
        }
    ]
}

# Test URL
url = "http://localhost:8000/api/pedidos/"

print("Testing POS API with corrected data structure...")
print(f"URL: {url}")
print(f"Data: {json.dumps(test_data, indent=2)}")
print("-" * 50)

try:
    response = requests.post(
        url,
        json=test_data,
        headers={
            'Content-Type': 'application/json',
            'X-CSRFToken': 'dummy'  # We'll handle CSRF in real requests
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200 or response.status_code == 201:
        print("✅ SUCCESS: API call successful!")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print("❌ ERROR: API call failed")
        print(f"Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ CONNECTION ERROR: {e}")
except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {e}")
