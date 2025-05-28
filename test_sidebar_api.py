#!/usr/bin/env python3
"""
Test script to verify the business configuration API endpoints
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_public_config():
    """Test the public configuration endpoint (no auth required)"""
    try:
        response = requests.get(f"{BASE_URL}/api/configuracion/publica/")
        print(f"Public Config Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Public Config Data:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception testing public config: {e}")

def test_business_config_authenticated():
    """Test the business configuration endpoint (auth required)"""
    # First, try without authentication
    try:
        response = requests.get(f"{BASE_URL}/api/configuracion/negocio/")
        print(f"Business Config (no auth) Status: {response.status_code}")
        if response.status_code == 401:
            print("✓ Correctly requires authentication")
        else:
            print(f"Unexpected response: {response.text}")
    except Exception as e:
        print(f"Exception testing business config: {e}")

def test_logo_endpoint():
    """Test the logo endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/configuracion/logotipo/")
        print(f"Logo endpoint Status: {response.status_code}")
        if response.status_code == 401:
            print("✓ Logo endpoint correctly requires authentication")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Exception testing logo endpoint: {e}")

def main():
    print("Testing Business Configuration API Endpoints")
    print("=" * 50)
    
    test_public_config()
    print()
    
    test_business_config_authenticated()
    print()
    
    test_logo_endpoint()
    print()
    
    print("Test completed!")

if __name__ == "__main__":
    main()
