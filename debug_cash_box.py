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

# Check API endpoints
print('=== Cash box API status ===')
resp = session.get('http://127.0.0.1:8000/api/cajas/')
print(f'GET /api/cajas/: {resp.status_code}')
if resp.status_code == 200:
    data = resp.json()
    if isinstance(data, dict) and 'results' in data:
        results = data['results']
    else:
        results = data if isinstance(data, list) else []
    print(f'Results: {len(results)} cash boxes')
    for caja in results:
        print(f'  ID: {caja.get("id")}, Tienda: {caja.get("tienda")}, Cerrada: {caja.get("cerrada")}')

# Check if we can get CSRF from different pages  
print('\n=== CSRF token sources ===')
for url in ['/caja/', '/ventas/pos/', '/dashboard/']:
    resp = session.get(f'http://127.0.0.1:8000{url}')
    print(f'GET {url}: {resp.status_code}')
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        if csrf_input:
            print(f'  CSRF found: {csrf_input.get("value")[:10]}...')
        else:
            print('  No CSRF input found')

# Try to create cash box
print('\n=== Attempting to create cash box ===')
resp = session.get('http://127.0.0.1:8000/ventas/pos/')
if resp.status_code == 200:
    soup = BeautifulSoup(resp.content, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    if csrf_input:
        csrf_token = csrf_input.get('value')
        print(f'Using CSRF: {csrf_token[:10]}...')
        
        cash_box_data = {
            'tienda': 1,
            'fondo_inicial': 1000.00
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token,
            'Referer': 'http://127.0.0.1:8000/ventas/pos/'
        }
        
        resp = session.post(
            'http://127.0.0.1:8000/api/cajas/',
            data=json.dumps(cash_box_data),
            headers=headers
        )
        
        print(f'POST /api/cajas/: {resp.status_code}')
        print(f'Response: {resp.text}')
    else:
        print('No CSRF token found')
