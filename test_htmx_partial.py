import requests

# Test HTMX search functionality
headers = {
    'HX-Request': 'true',
    'HX-Target': 'producto-table-container'
}

response = requests.get('http://127.0.0.1:8000/productos/?search=Nike', headers=headers)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type')}")
print(f"Content Length: {len(response.text)}")
print("\nPartial Template Response:")
print("=" * 50)
print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
