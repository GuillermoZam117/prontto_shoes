#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json

session = requests.Session()

# Login first
resp = session.get('http://127.0.0.1:8000/login/')
soup = BeautifulSoup(resp.content, 'html.parser')
csrf = soup.find('input', {'name': 'csrfmiddlewaretoken'}).get('value')
session.post('http://127.0.0.1:8000/login/', data={'username': 'admin', 'password': 'admin123', 'csrfmiddlewaretoken': csrf})

print('=== Checking current cash boxes ===')
# Check current cash boxes using the correct endpoint
resp = session.get('http://127.0.0.1:8000/api/caja/')
print(f'GET /api/caja/: {resp.status_code}')
if resp.status_code == 200:
    data = resp.json()
    if isinstance(data, dict) and 'results' in data:
        results = data['results']
    else:
        results = data if isinstance(data, list) else []
    print(f'Found {len(results)} cash boxes')
    for caja in results:
        print(f'  ID: {caja.get("id")}, Tienda: {caja.get("tienda")}, Cerrada: {caja.get("cerrada")}')
        if not caja.get("cerrada") and caja.get("tienda") == 1:
            print("✓ Cash box already open for store 1!")
            exit(0)

print('\n=== Opening cash box ===')
# Get CSRF from POS page
resp = session.get('http://127.0.0.1:8000/ventas/pos/')
if resp.status_code == 200:
    soup = BeautifulSoup(resp.content, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    if csrf_input:
        csrf_token = csrf_input.get('value')
        print(f'Using CSRF: {csrf_token[:10]}...')
        
        # Try using the specific open cash box endpoint
        cash_box_data = {
            'tienda_id': 1,
            'fondo_inicial': 1000.00
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token,
            'Referer': 'http://127.0.0.1:8000/ventas/pos/'
        }
        
        resp = session.post(
            'http://127.0.0.1:8000/api/caja/abrir_caja/',
            data=json.dumps(cash_box_data),
            headers=headers
        )
        
        print(f'POST /api/caja/abrir_caja/: {resp.status_code}')
        if resp.status_code == 201:
            print("✓ Cash box opened successfully!")
            print(f'Response: {resp.text}')
        elif resp.status_code == 400:
            response_data = resp.json()
            if 'already' in str(response_data).lower():
                print("✓ Cash box already exists!")
            else:
                print(f"✗ Error: {resp.text}")
        else:
            print(f'Response: {resp.text}')
            # Try fallback method using regular POST to /api/caja/
            print('\n--- Trying fallback method ---')
            cash_box_data = {
                'tienda': 1,
                'fondo_inicial': 1000.00,
                'cerrada': False
            }
            
            resp = session.post(
                'http://127.0.0.1:8000/api/caja/',
                data=json.dumps(cash_box_data),
                headers=headers
            )
            
            print(f'POST /api/caja/: {resp.status_code}')
            print(f'Response: {resp.text}')
    else:
        print('No CSRF token found')
