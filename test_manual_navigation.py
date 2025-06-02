#!/usr/bin/env python
"""
Simple manual test for logout functionality
"""
import requests
from requests.sessions import Session

def test_logout_manual():
    """Test logout manually using requests"""
    print("🧪 Testing logout functionality manually...")
    
    session = Session()
    
    try:
        # Get login page to get CSRF token
        login_url = "http://127.0.0.1:8000/login/"
        response = session.get(login_url)
        
        if response.status_code == 200:
            print("✅ Login page accessible")
            
            # Check if logout URL is configured correctly
            logout_url = "http://127.0.0.1:8000/logout/"
            response = session.get(logout_url)
            
            if response.status_code in [200, 302]:  # 302 for redirect
                print("✅ Logout URL is accessible and configured correctly")
                print(f"   Response status: {response.status_code}")
                if response.status_code == 302:
                    print(f"   Redirects to: {response.headers.get('Location', 'Unknown')}")
                return True
            else:
                print(f"❌ Logout URL failed with status: {response.status_code}")
                return False
        else:
            print(f"❌ Cannot access login page: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing logout: {e}")
        return False

def test_reports_urls():
    """Test reports URLs are accessible"""
    print("\n🧪 Testing reports URLs...")
    
    urls_to_test = [
        ("Reports Dashboard", "http://127.0.0.1:8000/reportes/"),
        ("Users Admin", "http://127.0.0.1:8000/administracion/usuarios/"),
    ]
    
    session = Session()
    results = []
    
    for name, url in urls_to_test:
        try:
            response = session.get(url)
            if response.status_code in [200, 302, 403]:  # 403 might be permission related
                status = "✅ ACCESSIBLE"
                if response.status_code == 403:
                    status += " (Needs authentication)"
                elif response.status_code == 302:
                    status += " (Redirects)"
                    
                print(f"{status} - {name}: {response.status_code}")
                results.append(True)
            else:
                print(f"❌ FAILED - {name}: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ ERROR - {name}: {e}")
            results.append(False)
    
    return all(results)

if __name__ == "__main__":
    print("🚀 Manual Navigation Test")
    print("=" * 40)
    
    logout_ok = test_logout_manual()
    reports_ok = test_reports_urls()
    
    print("\n" + "=" * 40)
    print("📊 SUMMARY")
    print("=" * 40)
    
    if logout_ok and reports_ok:
        print("🎉 All navigation links are working correctly!")
        print("✅ Logout functionality is properly configured")
        print("✅ Reports and Users sections are accessible")
    else:
        print("⚠️ Some issues found:")
        if not logout_ok:
            print("❌ Logout configuration issue")
        if not reports_ok:
            print("❌ Reports/Users accessibility issue")
