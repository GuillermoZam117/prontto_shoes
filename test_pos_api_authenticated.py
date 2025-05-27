#!/usr/bin/env python
"""
Test script to verify the POS API fix is working correctly with authentication.
This script simulates the frontend API call with proper authentication.
"""

import requests
import json
from datetime import date

# First, let's login to get the authentication token or session
login_url = "http://localhost:8000/accounts/login/"
api_url = "http://localhost:8000/api/pedidos/"

# Create a session to maintain cookies
session = requests.Session()

print("Testing POS API with authentication...")
print(f"Login URL: {login_url}")
print(f"API URL: {api_url}")
print("-" * 50)

try:
    # First get the login page to get CSRF token
    login_page = session.get(login_url)
    
    if login_page.status_code == 200:
        # Try to extract CSRF token from the page
        csrf_token = None
        if 'csrfmiddlewaretoken' in login_page.text:
            import re
            csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', login_page.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
        
        print(f"✅ Got login page, CSRF token: {csrf_token[:10]}..." if csrf_token else "❌ No CSRF token found")
        
        # Try to login with test credentials
        login_data = {
            'username': 'admin',  # Assuming admin user exists
            'password': 'admin',  # Common default password
            'csrfmiddlewaretoken': csrf_token
        } if csrf_token else {
            'username': 'admin',
            'password': 'admin'
        }
        
        # Attempt login
        login_response = session.post(login_url, data=login_data)
        print(f"Login attempt status: {login_response.status_code}")
        
        # Check if login was successful by trying to access a protected page
        pos_page = session.get("http://localhost:8000/ventas/pos/")
        print(f"POS page access status: {pos_page.status_code}")
        
        if pos_page.status_code == 200:
            print("✅ Successfully authenticated!")
            
            # Now test the API with the corrected data structure
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
            
            print(f"Testing API with data: {json.dumps(test_data, indent=2)}")
            
            # Get CSRF token from cookies
            csrf_token = session.cookies.get('csrftoken')
            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token,
                'Referer': 'http://localhost:8000/ventas/pos/'
            } if csrf_token else {
                'Content-Type': 'application/json'
            }
            
            response = session.post(api_url, json=test_data, headers=headers)
            
            print(f"API Status Code: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("✅ SUCCESS: API call successful!")
                print(f"Response: {json.dumps(response.json(), indent=2)}")
            elif response.status_code == 403:
                print("❌ FORBIDDEN: Still getting authentication error")
                print(f"Response: {response.text}")
            else:
                print("❌ ERROR: API call failed")
                print(f"Response: {response.text}")
                
        else:
            print("❌ Authentication failed - cannot access POS page")
            print("Try creating a superuser with: python manage.py createsuperuser")
            
    else:
        print(f"❌ Cannot access login page. Status: {login_page.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ CONNECTION ERROR: {e}")
except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {e}")
