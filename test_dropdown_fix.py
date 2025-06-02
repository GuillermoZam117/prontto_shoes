import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

def test_dropdown_functionality():
    """Test that dropdown menus work correctly"""
    print("🧪 Testing Dropdown Functionality...")
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1200,800")
    
    try:
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)
        
        # Navigate to the application
        print("📱 Opening application...")
        driver.get("http://127.0.0.1:8000/")
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.ID, "posSidebar")))
        print("✅ Application loaded successfully")
        
        # Find dropdown toggles
        dropdown_toggles = driver.find_elements(By.CSS_SELECTOR, ".nav-dropdown-toggle")
        print(f"📊 Found {len(dropdown_toggles)} dropdown toggles")
        
        if len(dropdown_toggles) == 0:
            print("❌ No dropdown toggles found!")
            return False
        
        success_count = 0
        
        for i, toggle in enumerate(dropdown_toggles):
            try:
                # Get dropdown name
                nav_text = toggle.find_element(By.CSS_SELECTOR, ".nav-text")
                dropdown_name = nav_text.text
                print(f"\n🔧 Testing dropdown: {dropdown_name}")
                
                # Get parent dropdown container
                dropdown_container = toggle.find_element(By.XPATH, "./ancestor::div[contains(@class, 'nav-dropdown')]")
                
                # Check initial state
                is_initially_open = "open" in dropdown_container.get_attribute("class")
                print(f"📊 Initial state: {'OPEN' if is_initially_open else 'CLOSED'}")
                
                # Click the dropdown toggle
                driver.execute_script("arguments[0].click();", toggle)
                time.sleep(0.5)  # Wait for animation
                
                # Check if dropdown opened
                is_now_open = "open" in dropdown_container.get_attribute("class")
                print(f"📊 After click: {'OPEN' if is_now_open else 'CLOSED'}")
                
                if is_initially_open != is_now_open:
                    print(f"✅ Dropdown '{dropdown_name}' toggled successfully!")
                    success_count += 1
                    
                    # Test dropdown menu visibility
                    dropdown_menu = dropdown_container.find_element(By.CSS_SELECTOR, ".nav-dropdown-menu")
                    if dropdown_menu.is_displayed():
                        print(f"✅ Dropdown menu for '{dropdown_name}' is visible")
                    else:
                        print(f"⚠️ Dropdown menu for '{dropdown_name}' is not visible")
                        
                    # Click again to close
                    driver.execute_script("arguments[0].click();", toggle)
                    time.sleep(0.5)
                    
                    is_closed = "open" not in dropdown_container.get_attribute("class")
                    if is_closed:
                        print(f"✅ Dropdown '{dropdown_name}' closed successfully!")
                    else:
                        print(f"❌ Dropdown '{dropdown_name}' failed to close!")
                else:
                    print(f"❌ Dropdown '{dropdown_name}' did not toggle!")
                    
            except Exception as e:
                print(f"❌ Error testing dropdown {i+1}: {str(e)}")
        
        # Test clicking outside to close dropdowns
        print(f"\n🧪 Testing click outside to close...")
        if dropdown_toggles:
            # Open first dropdown
            first_toggle = dropdown_toggles[0]
            driver.execute_script("arguments[0].click();", first_toggle)
            time.sleep(0.5)
            
            # Click outside
            sidebar = driver.find_element(By.ID, "posSidebar")
            actions = ActionChains(driver)
            actions.move_to_element_with_offset(sidebar, 10, 10).click().perform()
            time.sleep(0.5)
            
            # Check if dropdown closed
            dropdown_container = first_toggle.find_element(By.XPATH, "./ancestor::div[contains(@class, 'nav-dropdown')]")
            is_closed = "open" not in dropdown_container.get_attribute("class")
            if is_closed:
                print("✅ Click outside closed dropdown successfully!")
            else:
                print("❌ Click outside did not close dropdown!")
        
        print(f"\n📊 Test Results:")
        print(f"✅ Successful dropdowns: {success_count}/{len(dropdown_toggles)}")
        
        if success_count == len(dropdown_toggles):
            print("🎉 ALL DROPDOWN TESTS PASSED!")
            return True
        else:
            print("⚠️ Some dropdown tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    test_dropdown_functionality()
