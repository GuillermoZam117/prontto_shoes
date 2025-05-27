#!/usr/bin/env python
"""
Test script to make a request to the devolution detail page
"""
import requests

def test_devolution_page():
    url = "http://localhost:8000/devoluciones/1/"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Page loaded successfully!")
            print(f"Response length: {len(response.text)} characters")
        else:
            print(f"❌ Page failed to load")
            print(f"Response: {response.text[:500]}...")
            
    except Exception as e:
        print(f"Error making request: {e}")

if __name__ == "__main__":
    test_devolution_page()
