"""
Performance testing for Pronto Shoes POS system using Locust.
This file defines user behaviors for simulating load on critical API endpoints.
"""
import json
import random
from locust import HttpUser, task, between


class ProntoShoesPOSUser(HttpUser):
    """Simulates a POS user performing common operations."""
    
    # Wait between 1 and 3 seconds between tasks
    wait_time = between(1, 3)
    
    def on_start(self):
        """Log in at the start of the test."""
        # Authenticate and store the token for subsequent requests
        response = self.client.post(
            "/api/token/",
            json={"username": "locust_test", "password": "locust_pass"}
        )
        if response.status_code == 200:
            self.token = response.json().get("token", "")
            self.headers = {"Authorization": f"Token {self.token}"}
        else:
            self.token = ""
            self.headers = {}
    
    @task(5)
    def browse_products(self):
        """Browse products - high frequency task."""
        self.client.get("/api/productos/", headers=self.headers)
    
    @task(3)
    def view_inventory(self):
        """Check inventory levels - moderate frequency task."""
        self.client.get("/api/inventario/", headers=self.headers)
    
    @task(3)
    def search_products(self):
        """Search for products - moderate frequency task."""
        # Simulate different search terms
        search_terms = ["zapato", "bota", "sandalia", "negro", "44"]
        term = random.choice(search_terms)
        self.client.get(f"/api/productos/?search={term}", headers=self.headers)
    
    @task(2)
    def view_client_info(self):
        """Look up client information - moderate frequency task."""
        # Assuming there are clients with IDs 1-10
        client_id = random.randint(1, 10)
        self.client.get(f"/api/clientes/{client_id}/", headers=self.headers)
    
    @task(1)
    def create_order(self):
        """Create a new order - less frequent, but intensive task."""
        client_id = random.randint(1, 10)
        product_id = random.randint(1, 20)
        
        # First get store ID
        store_response = self.client.get("/api/tiendas/", headers=self.headers)
        if store_response.status_code != 200:
            return
        
        stores = store_response.json()
        if not stores:
            return
            
        store_id = stores[0]["id"] if stores else 1
        
        order_data = {
            "cliente": client_id,
            "tienda": store_id,
            "estado": "pendiente",
            "total": random.uniform(500, 3000),
            "tipo": "venta",
            "descuento_aplicado": 0
        }
        
        # Create order
        order_response = self.client.post(
            "/api/pedidos/", 
            json=order_data,
            headers=self.headers
        )
        
        if order_response.status_code != 201:
            return
            
        order = order_response.json()
        
        # Add order details
        detail_data = {
            "pedido": order["id"],
            "producto": product_id,
            "cantidad": random.randint(1, 3),
            "precio_unitario": random.uniform(300, 1000),
            "subtotal": random.uniform(300, 3000)
        }
        
        self.client.post(
            "/api/detalles-pedido/", 
            json=detail_data,
            headers=self.headers
        )
    
    @task(1)
    def run_sales_report(self):
        """Generate sales report - resource-intensive task."""
        self.client.get("/api/reportes/pedidos_por_surtir/", headers=self.headers)
    
    @task(1)
    def run_inventory_report(self):
        """Generate inventory report - resource-intensive task."""
        self.client.get("/api/inventario/?tienda=1", headers=self.headers)


class MobileAppUser(HttpUser):
    """Simulates a mobile app user with different patterns."""
    
    wait_time = between(3, 10)  # Mobile users have more delay between actions
    
    def on_start(self):
        """Log in at the start of the test."""
        response = self.client.post(
            "/api/token/",
            json={"username": "mobile_user", "password": "mobile_pass"}
        )
        if response.status_code == 200:
            self.token = response.json().get("token", "")
            self.headers = {"Authorization": f"Token {self.token}"}
        else:
            self.token = ""
            self.headers = {}
    
    @task(10)
    def browse_products_mobile(self):
        """Browse products - the main activity on mobile."""
        self.client.get("/api/productos/", headers=self.headers)
    
    @task(5)
    def search_products_mobile(self):
        """Search for products on mobile."""
        search_terms = ["zapato", "bota", "sandalia", "negro", "44"]
        term = random.choice(search_terms)
        self.client.get(f"/api/productos/?search={term}", headers=self.headers)
    
    @task(2)
    def view_order_status(self):
        """Check order status."""
        # Assume orders with IDs 1-20
        order_id = random.randint(1, 20)
        self.client.get(f"/api/pedidos/{order_id}/", headers=self.headers) 