#!/usr/bin/env python3
"""
Debug script to test sidebar dropdown functionality
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def debug_sidebar_dropdown():
    """Test sidebar dropdown functionality"""
    print("🔍 Starting sidebar dropdown debug...")
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless Chrome
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)
        
        # Navigate to login page first
        print("📱 Navigating to login page...")
        driver.get("http://localhost:8000/auth/login/")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Log in (assuming admin credentials)
        username_field = driver.find_element(By.NAME, "username")
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys("admin")
        password_field.send_keys("admin123")
        
        # Submit login form
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Wait for redirect to dashboard
        time.sleep(2)
        
        print("✅ Logged in successfully")
        
        # Check if sidebar elements exist
        print("🔍 Checking sidebar elements...")
        
        try:
            sidebar = driver.find_element(By.ID, "posSidebar")
            print("✅ Sidebar found")
        except:
            print("❌ Sidebar not found")
            return
        
        # Check for dropdown toggles
        try:
            dropdown_toggles = driver.find_elements(By.CSS_SELECTOR, ".nav-dropdown-toggle")
            print(f"✅ Found {len(dropdown_toggles)} dropdown toggles")
            
            for i, toggle in enumerate(dropdown_toggles):
                parent = toggle.find_element(By.XPATH, "..")
                nav_text = toggle.find_element(By.CSS_SELECTOR, ".nav-text").text
                print(f"  - Dropdown {i+1}: {nav_text}")
                print(f"    Classes: {parent.get_attribute('class')}")
                
        except Exception as e:
            print(f"❌ Error finding dropdown toggles: {e}")
            return
        
        # Test clicking on dropdowns
        print("🔍 Testing dropdown clicks...")
        
        for i, toggle in enumerate(dropdown_toggles):
            try:
                nav_text = toggle.find_element(By.CSS_SELECTOR, ".nav-text").text
                print(f"🖱️ Clicking on '{nav_text}' dropdown...")
                
                # Scroll to element to make sure it's visible
                driver.execute_script("arguments[0].scrollIntoView(true);", toggle)
                time.sleep(0.5)
                
                # Get parent dropdown before click
                parent_dropdown = toggle.find_element(By.XPATH, "..")
                classes_before = parent_dropdown.get_attribute('class')
                print(f"   Classes before click: {classes_before}")
                
                # Click the toggle
                driver.execute_script("arguments[0].click();", toggle)
                time.sleep(1)
                
                # Check classes after click
                classes_after = parent_dropdown.get_attribute('class')
                print(f"   Classes after click: {classes_after}")
                
                # Check if 'open' class was added
                if 'open' in classes_after and 'open' not in classes_before:
                    print(f"✅ Dropdown '{nav_text}' opened successfully")
                else:
                    print(f"❌ Dropdown '{nav_text}' did not open")
                
                # Check if menu is visible
                try:
                    menu = parent_dropdown.find_element(By.CSS_SELECTOR, ".nav-dropdown-menu")
                    menu_height = menu.value_of_css_property("max-height")
                    print(f"   Menu max-height: {menu_height}")
                except Exception as e:
                    print(f"   ❌ Error checking menu: {e}")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error testing dropdown {i+1}: {e}")
        
        # Check JavaScript console for errors
        print("🔍 Checking JavaScript console...")
        logs = driver.get_log('browser')
        if logs:
            print("📋 Console logs:")
            for log in logs:
                print(f"   {log['level']}: {log['message']}")
        else:
            print("✅ No console errors found")
            
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    debug_sidebar_dropdown()
