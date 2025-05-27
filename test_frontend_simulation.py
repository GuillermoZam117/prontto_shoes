#!/usr/bin/env python3
"""
Frontend simulation test for store fix verification
"""
import requests
import json

def test_frontend_simulation():
    """Simulate the frontend request with store 1"""
    
    # Base URL
    base_url = "http://127.0.0.1:8000"
    
    # Start session
    session = requests.Session()
    
    # Get CSRF token from login page
    login_url = f"{base_url}/admin/login/"
    response = session.get(login_url)
    print(f"Login page status: {response.status_code}")
    
    # Extract CSRF token
    csrf_token = None
    if 'csrftoken' in session.cookies:
        csrf_token = session.cookies['csrftoken']
    else:
        print("❌ No CSRF token found")
        return False
    
    print(f"✅ CSRF token: {csrf_token[:10]}...")
    
    # Login as admin
    login_data = {
        'username': 'admin',
        'password': 'admin123',
        'csrfmiddlewaretoken': csrf_token
    }
    
    response = session.post(login_url, data=login_data)
    print(f"Login response: {response.status_code}")
    
    # Navigate to POS page
    pos_url = f"{base_url}/ventas/pos/"
    response = session.get(pos_url)
    print(f"POS page status: {response.status_code}")    # Simulate order creation with store 1
    order_data = {
        'fecha': '2025-05-27',
        'tipo': 'venta',  # Back to venta
        'tienda': 1,  # Store 1 has open cash box
        'cliente': 2,  # Different client ID to avoid duplicate order error
        'pagado': True,
        'total': 150.00,
        'detalles': [
            {
                'producto': 1,  # Assuming product ID 1 exists
                'cantidad': 1,
                'precio_unitario': 150.00,
                'subtotal': 150.00
            }
        ]
    }
    
    # Get fresh CSRF token
    if 'csrftoken' in session.cookies:
        csrf_token = session.cookies['csrftoken']
    
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token,
        'Referer': pos_url
    }
      # Make the API request
    api_url = f"{base_url}/api/pedidos/"
    response = session.post(api_url, data=json.dumps(order_data), headers=headers)
    
    print(f"API response status: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Order created successfully!")
        print(f"Order ID: {data.get('id')}")
        print(f"Store: {data.get('tienda')}")
        print(f"Total: ${data.get('total')}")
        return True
    else:
        print(f"❌ Order creation failed")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    print("=== FRONTEND SIMULATION TEST ===")
    print("Testing order creation with store 1 (has open cash box)...")
    
    try:
        success = test_frontend_simulation()
        if success:
            print("\n🎉 STORE FIX SUCCESSFUL!")
            print("Frontend can now create orders using store 1.")
        else:
            print("\n❌ STORE FIX NEEDS MORE WORK")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
