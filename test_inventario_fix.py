#!/usr/bin/env python3
"""
Test script to verify that the inventario template syntax error has been fixed.
Tests both the full page load and HTMX partial requests.
"""

import requests
import sys

def test_inventario_pages():
    """Test inventario page loads and HTMX functionality"""
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing Inventario Template Fix...")
    print("=" * 50)
    
    # Test 1: Full page load
    print("\n1. Testing full inventario page load...")
    try:
        response = requests.get(f"{base_url}/inventario/")
        if response.status_code == 200:
            print("✅ Full page loads successfully (200 OK)")
            if "TemplateSyntaxError" in response.text:
                print("❌ Template syntax error still present")
                return False
            else:
                print("✅ No template syntax errors detected")
        else:
            print(f"❌ Full page failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error loading full page: {e}")
        return False
    
    # Test 2: HTMX search request
    print("\n2. Testing HTMX search functionality...")
    try:
        headers = {
            'HX-Request': 'true',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.get(f"{base_url}/inventario/?q=test", headers=headers)
        if response.status_code == 200:
            print("✅ HTMX search request successful (200 OK)")
            if "TemplateSyntaxError" in response.text:
                print("❌ Template syntax error in HTMX response")
                return False
            else:
                print("✅ HTMX response has no template syntax errors")
        else:
            print(f"❌ HTMX search failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error with HTMX search: {e}")
        return False
    
    # Test 3: Check for specific template content
    print("\n3. Verifying template content...")
    try:
        response = requests.get(f"{base_url}/inventario/")
        content = response.text
        
        # Check that our fix is working (should have stock_normal_count)
        if "stock_normal_count" in content or "Stock Normal" in content:
            print("✅ Template contains expected content")
        else:
            print("⚠️  Expected content not found (might be empty data)")
        
        # Verify no invalid template syntax
        invalid_patterns = [
            "{% empty %}{% endfor %}",
            "{% for item in inventario %}{% if",
            "TemplateSyntaxError"
        ]
        
        for pattern in invalid_patterns:
            if pattern in content:
                print(f"❌ Found invalid pattern: {pattern}")
                return False
        
        print("✅ No invalid template patterns detected")
        
    except Exception as e:
        print(f"❌ Error checking template content: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED! Inventario template syntax error is FIXED!")
    return True

if __name__ == "__main__":
    success = test_inventario_pages()
    sys.exit(0 if success else 1)
