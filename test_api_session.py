#!/usr/bin/env python
"""
Test script to verify the API authentication is working correctly.
This simulates what the frontend should be doing.
"""

import requests
import json
import re

# Start a session to maintain cookies
session = requests.Session()

# First, get the login page to retrieve CSRF token
login_url = 'http://127.0.0.1:8000/login/'
print("1. Getting login page...")
response = session.get(login_url)
print(f"Login page status: {response.status_code}")

# Extract CSRF token using regex (more reliable)
csrf_pattern = r'name="csrfmiddlewaretoken" value="([^"]+)"'
csrf_match = re.search(csrf_pattern, response.text)

if not csrf_match:
    print("ERROR: Could not find CSRF token in login page")
    exit(1)

csrf_token = csrf_match.group(1)
print(f"Found CSRF token: {csrf_token[:10]}...")

# Print cookies to debug
print(f"Session cookies after login page: {session.cookies}")

# Now login with admin credentials
print("\n2. Logging in...")
login_data = {
    'username': 'admin',
    'password': 'admin123',
    'csrfmiddlewaretoken': csrf_token,
    'next': '/dashboard/',  # Add next parameter like the form does
}

login_response = session.post(login_url, data=login_data, allow_redirects=False)
print(f"Login response status: {login_response.status_code}")
print(f"Login response headers: {dict(login_response.headers)}")
print(f"Session cookies after login: {session.cookies}")

if login_response.status_code == 302:
    redirect_location = login_response.headers.get('Location', '')
    print(f"✓ Login successful! Redirected to: {redirect_location}")
    
    # Follow the redirect
    if redirect_location:
        if redirect_location.startswith('/'):
            redirect_url = f'http://127.0.0.1:8000{redirect_location}'
        else:
            redirect_url = redirect_location
        dashboard_response = session.get(redirect_url)
        print(f"Dashboard response status: {dashboard_response.status_code}")
else:
    print(f"✗ Login failed.")
    print(f"Response text: {login_response.text[:500]}...")  # First 500 chars

# Now get the POS page to get a fresh CSRF token
print("\n3. Getting POS page...")
pos_url = 'http://127.0.0.1:8000/ventas/pos/'
pos_response = session.get(pos_url)
print(f"POS page status: {pos_response.status_code}")

if pos_response.status_code != 200:
    print(f"✗ Cannot access POS page. Response: {pos_response.text[:500]}...")
    exit(1)

# Extract fresh CSRF token
csrf_match = re.search(csrf_pattern, pos_response.text)
if csrf_match:
    csrf_token = csrf_match.group(1)
    print(f"Found fresh CSRF token: {csrf_token[:10]}...")
else:
    print("WARNING: Could not find fresh CSRF token")

# Now test the API call
print("\n4. Testing API call...")
api_url = 'http://127.0.0.1:8000/api/pedidos/'

# First, let's check if we can access the API without authentication
print("4a. Testing API access without authentication...")
test_response = session.get(api_url)
print(f"API GET response status: {test_response.status_code}")
if test_response.status_code != 200:
    print(f"API GET response: {test_response.text}")

# Now test the POST
print("4b. Testing API POST...")

# First, let's check what products and stores exist
print("4a. Checking available products and stores...")

# Get products
products_response = session.get('http://127.0.0.1:8000/api/productos/')
print(f"Products API status: {products_response.status_code}")
if products_response.status_code == 200:
    products = products_response.json()
    print(f"Found {len(products)} products")
    if products:
        product = products[0]
        print(f"Using product: {product.get('id')} - {product.get('codigo')} - {product.get('precio', 'No price')}")
    else:
        print("No products found!")
        exit(1)
else:
    print(f"Failed to get products: {products_response.text}")
    exit(1)

# Get stores
stores_response = session.get('http://127.0.0.1:8000/api/tiendas/')
print(f"Stores API status: {stores_response.status_code}")
if stores_response.status_code == 200:
    stores = stores_response.json()
    print(f"Found {len(stores)} stores")
    if stores:
        store = stores[0]
        print(f"Using store: {store.get('id')} - {store.get('nombre')}")
    else:
        print("No stores found!")
        exit(1)
else:
    print(f"Failed to get stores: {stores_response.text}")
    exit(1)

# Get clients
clients_response = session.get('http://127.0.0.1:8000/api/clientes/')
print(f"Clients API status: {clients_response.status_code}")
if clients_response.status_code == 200:
    clients = clients_response.json()
    print(f"Found {len(clients)} clients")
    if clients:
        client = clients[0]
        print(f"Using client: {client.get('id')} - {client.get('nombre')}")
    else:
        client = None
        print("No clients found, will use 'Público en General'")
else:
    client = None
    print(f"Failed to get clients, will use 'Público en General': {clients_response.text}")

print("\n4b. Testing API POST with correct data structure...")

# Calculate required fields based on the product
precio_unitario = float(product.get('precio', 100.0))
cantidad = 1
subtotal = precio_unitario * cantidad

# Create the correct data structure based on the backend serializer
test_data = {
    'fecha': '2025-05-27',
    'tipo': 'venta',
    'tienda': store['id'],
    'pagado': True,
    'total': subtotal,  # Required field
    'detalles': [
        {
            'producto': product['id'],
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,  # Required field
            'subtotal': subtotal  # Required field
            # Note: 'pedido' field will be set by the backend when creating DetallePedido
        }
    ]
}

# Add cliente only if we have one (backend handles "Público en General" automatically)
if client:
    test_data['cliente'] = client['id']

headers = {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrf_token,
    'Referer': pos_url,  # Some servers require this
}

print(f"Sending data: {json.dumps(test_data, indent=2)}")
print(f"Headers: {headers}")
print(f"Session cookies: {session.cookies}")

api_response = session.post(api_url, json=test_data, headers=headers)
print(f"\nAPI response status: {api_response.status_code}")
print(f"API response headers: {dict(api_response.headers)}")

if api_response.status_code == 200 or api_response.status_code == 201:
    print("✓ API call successful!")
    try:
        response_data = api_response.json()
        print(f"Response data: {json.dumps(response_data, indent=2)}")
    except:
        print(f"Response text: {api_response.text}")
else:
    print(f"✗ API call failed!")
    print(f"Response text: {api_response.text}")

print("\n=== Summary ===")
print(f"Login: {'✓' if login_response.status_code == 302 else '✗'}")
print(f"POS Page: {'✓' if pos_response.status_code == 200 else '✗'}")
print(f"API Call: {'✓' if api_response.status_code in [200, 201] else '✗'}")
