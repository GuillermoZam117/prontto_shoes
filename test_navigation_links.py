#!/usr/bin/env python
"""
Test script to verify navigation links in sidebar
"""
import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

def setup_driver():
    """Setup Chrome driver with options"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"❌ Error setting up Chrome driver: {e}")
        return None

def login_user(driver, username="admin", password="admin123"):
    """Login to the system"""
    try:
        driver.get("http://127.0.0.1:8000/login/")
        wait = WebDriverWait(driver, 10)
        
        # Wait for login form
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        # Submit form
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Wait for redirect to dashboard
        wait.until(EC.url_contains("dashboard"))
        print("✅ Successfully logged in")
        return True
        
    except TimeoutException:
        print("❌ Login timeout - check if server is running")
        return False
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

def test_dropdown_functionality(driver):
    """Test that dropdowns open and close correctly"""
    try:
        wait = WebDriverWait(driver, 10)
        
        print("\n🧪 Testing dropdown functionality...")
        
        # Test Reportes dropdown
        reportes_toggle = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Reportes']/parent::a")))
        reportes_toggle.click()
        time.sleep(1)
        
        reportes_menu = wait.until(EC.visibility_of_element_located((By.XPATH, "//span[text()='Reportes']/ancestor::div[@class='nav-item nav-dropdown']//div[@class='nav-dropdown-menu']")))
        print("✅ Reportes dropdown opens")
        
        # Test Administración dropdown
        admin_toggle = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Administración']/parent::a")))
        admin_toggle.click()
        time.sleep(1)
        
        admin_menu = wait.until(EC.visibility_of_element_located((By.XPATH, "//span[text()='Administración']/ancestor::div[@class='nav-item nav-dropdown']//div[@class='nav-dropdown-menu']")))
        print("✅ Administración dropdown opens")
        
        return True
        
    except Exception as e:
        print(f"❌ Dropdown test failed: {e}")
        return False

def test_navigation_links(driver):
    """Test navigation links"""
    links_to_test = [
        {
            'name': 'Dashboard de Reportes',
            'xpath': "//span[text()='Dashboard de Reportes']/parent::a",
            'expected_url_contains': 'reportes'
        },
        {
            'name': 'Usuarios',
            'xpath': "//span[text()='Usuarios']/parent::a",
            'expected_url_contains': 'administracion/usuarios'
        },
        {
            'name': 'Cerrar Sesión',
            'xpath': "//span[text()='Cerrar Sesión']/parent::a",
            'expected_url_contains': 'login'
        }
    ]
    
    results = []
    
    for link_info in links_to_test:
        try:
            print(f"\n🧪 Testing {link_info['name']} link...")
            
            # Go back to dashboard first
            driver.get("http://127.0.0.1:8000/dashboard/")
            wait = WebDriverWait(driver, 10)
            time.sleep(2)
            
            # Open appropriate dropdown if needed
            if link_info['name'] in ['Dashboard de Reportes']:
                reportes_toggle = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Reportes']/parent::a")))
                reportes_toggle.click()
                time.sleep(1)
            elif link_info['name'] in ['Usuarios', 'Cerrar Sesión']:
                admin_toggle = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Administración']/parent::a")))
                admin_toggle.click()
                time.sleep(1)
            
            # Click the link
            link = wait.until(EC.element_to_be_clickable((By.XPATH, link_info['xpath'])))
            current_url = driver.current_url
            link.click()
            
            # Wait for navigation
            wait.until(lambda driver: driver.current_url != current_url)
            new_url = driver.current_url
            
            if link_info['expected_url_contains'] in new_url:
                print(f"✅ {link_info['name']} link works - navigated to: {new_url}")
                results.append({'name': link_info['name'], 'status': 'PASS', 'url': new_url})
            else:
                print(f"❌ {link_info['name']} link failed - expected URL to contain '{link_info['expected_url_contains']}', got: {new_url}")
                results.append({'name': link_info['name'], 'status': 'FAIL', 'url': new_url})
                
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error testing {link_info['name']}: {e}")
            results.append({'name': link_info['name'], 'status': 'ERROR', 'error': str(e)})
    
    return results

def main():
    """Main test function"""
    print("🚀 Starting Navigation Links Test")
    print("=" * 50)
    
    # Setup driver
    driver = setup_driver()
    if not driver:
        return
    
    try:
        # Login
        if not login_user(driver):
            return
        
        # Test dropdowns
        test_dropdown_functionality(driver)
        
        # Test navigation links
        results = test_navigation_links(driver)
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for r in results if r['status'] == 'PASS')
        failed = sum(1 for r in results if r['status'] == 'FAIL')
        errors = sum(1 for r in results if r['status'] == 'ERROR')
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"🔥 Errors: {errors}")
        
        for result in results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "🔥"
            print(f"{status_icon} {result['name']}: {result['status']}")
            if 'url' in result:
                print(f"   → {result['url']}")
            if 'error' in result:
                print(f"   → {result['error']}")
        
        if failed == 0 and errors == 0:
            print("\n🎉 All tests passed! Navigation links are working correctly.")
        else:
            print(f"\n⚠️  {failed + errors} tests failed. Check the issues above.")
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        
    finally:
        driver.quit()
        print("\n🏁 Test completed")

if __name__ == "__main__":
    main()
