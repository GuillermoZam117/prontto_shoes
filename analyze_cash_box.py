#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

session = requests.Session()

# Login first
resp = session.get('http://127.0.0.1:8000/login/')
soup = BeautifulSoup(resp.content, 'html.parser')
csrf = soup.find('input', {'name': 'csrfmiddlewaretoken'}).get('value')
session.post('http://127.0.0.1:8000/login/', data={'username': 'admin', 'password': 'admin123', 'csrfmiddlewaretoken': csrf})

print('=== Detailed cash box analysis ===')
resp = session.get('http://127.0.0.1:8000/api/caja/')
if resp.status_code == 200:
    data = resp.json()
    if isinstance(data, dict) and 'results' in data:
        results = data['results']
    else:
        results = data if isinstance(data, list) else []
    
    print(f'Total cash boxes: {len(results)}')
    
    # Filter for store 1
    store_1_boxes = [c for c in results if c.get('tienda') == 1]
    print(f'Cash boxes for store 1: {len(store_1_boxes)}')
    
    # Show recent ones
    for caja in store_1_boxes[-5:]:  # Last 5
        print(f'  ID: {caja.get("id")}, Date: {caja.get("fecha", "N/A")}, Closed: {caja.get("cerrada")}, Initial: {caja.get("fondo_inicial")}')
    
    # Check today's cash boxes specifically
    today = datetime.now().strftime('%Y-%m-%d')
    print(f'\nChecking for today ({today}):')
    today_boxes = [c for c in store_1_boxes if c.get('fecha') == today]
    print(f'Today\'s cash boxes for store 1: {len(today_boxes)}')
    
    for caja in today_boxes:
        print(f'  ID: {caja.get("id")}, Closed: {caja.get("cerrada")}, Initial: {caja.get("fondo_inicial")}')
    
    # Check if there's an open cash box for today
    open_today = [c for c in today_boxes if not c.get('cerrada')]
    print(f'Open cash boxes today: {len(open_today)}')
    
    if not open_today:
        print('\n=== Opening cash box for today ===')
        # Get CSRF from POS page
        resp = session.get('http://127.0.0.1:8000/ventas/pos/')
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
            if csrf_input:
                csrf_token = csrf_input.get('value')
                
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
                
                print(f'Open cash box response: {resp.status_code}')
                print(f'Response: {resp.text}')
    else:
        print('✓ Found open cash box for today!')
else:
    print(f'Error getting cash boxes: {resp.status_code}')
    print(resp.text)
