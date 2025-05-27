#!/usr/bin/env python3
"""
Script to open a cash box for testing order creation
"""
import requests
import json
from bs4 import BeautifulSoup

def open_cash_box():
    base_url = 'http://127.0.0.1:8000'
    session = requests.Session()
      print("1. Getting login page...")
    response = session.get(f'{base_url}/login/')
    if response.status_code != 200:
        print(f"Failed to get login page: {response.status_code}")
        return False
    
    soup = BeautifulSoup(response.content, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrftoken'})
    if not csrf_input:
        # Try alternative ways to find CSRF token
        csrf_input = soup.find('input', attrs={'name': 'csrfmiddlewaretoken'})
        if not csrf_input:
            # Try meta tag
            csrf_meta = soup.find('meta', attrs={'name': 'csrf-token'})
            if csrf_meta:
                csrf_token = csrf_meta['content']
            else:
                print("Could not find CSRF token")
                return False
        else:
            csrf_token = csrf_input['value']
    else:
        csrf_token = csrf_input['value']
    print(f"Found CSRF token: {csrf_token[:10]}...")
    
    print("2. Logging in...")
    login_data = {
        'username': 'admin',
        'password': 'admin123',
        'csrfmiddlewaretoken': csrf_token
    }
    
    response = session.post(f'{base_url}/login/', data=login_data)
    if response.status_code != 302:
        print(f"Login failed: {response.status_code}")
        return False
    
    print("✓ Login successful!")
    
    print("3. Opening cash box...")
    
    # Get fresh CSRF token for API call
    response = session.get(f'{base_url}/ventas/pos/')
    soup = BeautifulSoup(response.content, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
    
    # Open cash box via API
    cash_box_data = {
        'tienda_id': 1,  # Tienda01
        'fondo_inicial': 1000.00  # Starting with $1000
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token,
        'Referer': f'{base_url}/ventas/pos/'
    }
    
    response = session.post(
        f'{base_url}/api/cajas/abrir_caja/',
        data=json.dumps(cash_box_data),
        headers=headers
    )
    
    print(f"Cash box API response status: {response.status_code}")
    
    if response.status_code == 201:
        print("✓ Cash box opened successfully!")
        response_data = response.json()
        print(f"Cash box ID: {response_data.get('id')}")
        print(f"Store: {response_data.get('tienda')}")
        print(f"Initial fund: ${response_data.get('fondo_inicial')}")
        return True
    elif response.status_code == 409:
        print("✓ Cash box already exists for this store today!")
        return True
    else:
        print(f"✗ Failed to open cash box: {response.status_code}")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    success = open_cash_box()
    if success:
        print("\n=== Ready to test order creation! ===")
        print("Cash box is now open. You can run the order test script.")
    else:
        print("\n=== Cash box opening failed ===")
        print("Please check the error messages above.")
