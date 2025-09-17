#!/usr/bin/env python3
"""
Amazon Login Component
Step-by-step login process with debug output
"""

from patchright.sync_api import sync_playwright
import time

class AmazonLoginComponent:
    def __init__(self, headless=False):
        self.headless = headless
        self.browser = None
        self.page = None
        
        # Load credentials
        with open('credentials.txt', 'r') as f:
            lines = f.read().strip().split('\n')
            self.email = lines[0]
            self.password = lines[1]
    
    def start_browser(self):
        """Start the browser"""
        print("🚀 Starting browser...")
        try:
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page()
            print("✅ Browser started")
            return True
        except Exception as e:
            print(f"❌ Failed to start browser: {e}")
            return False
    
    def close_browser(self):
        """Close the browser"""
        if self.browser:
            self.browser.close()
            print("🔒 Browser closed")
    
    def step1_enter_homepage(self):
        """Step 1: Enter Amazon homepage"""
        print("\n📍 Step 1: Entering Amazon homepage...")
        try:
            self.page.goto('https://www.amazon.com/', wait_until='domcontentloaded', timeout=15000)
            time.sleep(1)
            print(f"✅ Navigated to: {self.page.url}")
            print(f"✅ Page title: {self.page.title()}")
            
            # Check if we need to click "Continue shopping"
            continue_shopping_selectors = [
                'button:has-text("Continue shopping")',
                'a:has-text("Continue shopping")',
                'input[value="Continue shopping"]',
                'button[type="submit"]',
                'input[type="submit"]'
            ]
            
            for selector in continue_shopping_selectors:
                try:
                    element = self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        text = element.text_content().strip()
                        print(f"🔍 Found continue shopping button: '{text}' using selector: {selector}")
                        self.page.click(selector)
                        time.sleep(1)
                        print(f"✅ Clicked continue shopping, current URL: {self.page.url}")
                        print(f"✅ New page title: {self.page.title()}")
                        break
                except:
                    continue
            
            return True
        except Exception as e:
            print(f"❌ Error navigating to homepage: {e}")
            return False
    
    def step2_check_sign_in(self):
        """Step 2: Check if sign in is visible"""
        print("\n📍 Step 2: Checking for sign in button...")
        try:
            # Look for sign in elements
            signin_selectors = [
                'a[data-nav-role="signin"]',
                'a:has-text("Sign in")',
                'a:has-text("Sign In")',
                '#nav-link-accountList',
                'a[href*="/ap/signin"]'
            ]
            
            for selector in signin_selectors:
                try:
                    element = self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        text = element.text_content().strip()
                        print(f"✅ Found sign in element: '{text}' using selector: {selector}")
                        return True, element, selector
                except:
                    continue
            
            print("✅ No sign in button found - user is already logged in")
            return False, None, None
            
        except Exception as e:
            print(f"❌ Error checking sign in: {e}")
            return False, None, None
    
    def step3_hover_and_click(self, element, selector):
        """Step 3: Hover over sign in and click yellow button"""
        print("\n📍 Step 3: Hovering over sign in and clicking...")
        try:
            # Hover over the element
            element.hover()
            time.sleep(0.5)
            print("✅ Hovered over sign in element")
            
            # Look for yellow sign in button in dropdown
            yellow_button_selectors = [
                'a:has-text("Sign in")',
                'a:has-text("Sign In")',
                'a[href*="/ap/signin"]',
                '.nav-action-inner',
                '.nav-action-button'
            ]
            
            for btn_selector in yellow_button_selectors:
                try:
                    btn_element = self.page.wait_for_selector(btn_selector, timeout=2000)
                    if btn_element:
                        btn_text = btn_element.text_content().strip()
                        print(f"✅ Found yellow button: '{btn_text}' using selector: {btn_selector}")
                        self.page.click(btn_selector)
                        time.sleep(1)
                        print(f"✅ Clicked yellow button, current URL: {self.page.url}")
                        return True
                except:
                    continue
            
            # If no yellow button found, try clicking the original element
            print("⚠️ No yellow button found, clicking original element...")
            self.page.click(selector)
            time.sleep(1)
            print(f"✅ Clicked original element, current URL: {self.page.url}")
            return True
            
        except Exception as e:
            print(f"❌ Error hovering and clicking: {e}")
            return False
    
    def step4_enter_email(self):
        """Step 4: Enter email"""
        print("\n📍 Step 4: Entering email...")
        try:
            # Wait for email input
            email_selectors = ['#ap_email', 'input[name="email"]', 'input[type="email"]']
            
            for selector in email_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000)
                    self.page.fill(selector, self.email)
                    print(f"✅ Email entered using selector: {selector}")
                    return True
                except:
                    continue
            
            print("❌ Could not find email input field")
            return False
            
        except Exception as e:
            print(f"❌ Error entering email: {e}")
            return False
    
    def step5_click_continue(self):
        """Step 5: Click continue"""
        print("\n📍 Step 5: Clicking continue...")
        try:
            continue_selectors = ['#continue', 'input[type="submit"]', 'button[type="submit"]']
            
            for selector in continue_selectors:
                try:
                    self.page.click(selector)
                    print(f"✅ Continue clicked using selector: {selector}")
                    time.sleep(0.5)
                    return True
                except:
                    continue
            
            print("⚠️ Could not find continue button, trying Enter key")
            self.page.keyboard.press('Enter')
            time.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"❌ Error clicking continue: {e}")
            return False
    
    def step6_enter_password(self):
        """Step 6: Enter password"""
        print("\n📍 Step 6: Entering password...")
        try:
            password_selectors = ['input[name="password"]', 'input[type="password"]', '#ap_password']
            
            for selector in password_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000)
                    self.page.fill(selector, self.password)
                    time.sleep(0.3)  # Small wait to ensure field is filled
                    print(f"✅ Password entered using selector: {selector}")
                    return True
                except:
                    continue
            
            print("❌ Could not find password input field")
            return False
            
        except Exception as e:
            print(f"❌ Error entering password: {e}")
            return False
    
    def step7_click_sign_in(self):
        """Step 7: Click sign in"""
        print("\n📍 Step 7: Clicking sign in...")
        try:
            signin_selectors = ['#continue', '#signInSubmit', 'input[type="submit"]', 'button[type="submit"]']
            
            for selector in signin_selectors:
                try:
                    self.page.click(selector)
                    print(f"✅ Sign in clicked using selector: {selector}")
                    time.sleep(1)  # Wait for login to complete
                    return True
                except:
                    continue
            
            print("⚠️ Could not find sign in button, trying Enter key")
            self.page.keyboard.press('Enter')
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"❌ Error clicking sign in: {e}")
            return False
    
    def step8_check_success(self):
        """Step 8: Check if login was successful"""
        print("\n📍 Step 8: Checking login success...")
        try:
            current_url = self.page.url
            page_title = self.page.title()
            
            print(f"Current URL: {current_url}")
            print(f"Page title: {page_title}")
            
            # Check if redirected to success page
            if 'ref_=nav_signin' in current_url and 'amazon.com' in current_url:
                print("✅ Login successful! Redirected to nav_signin page")
                return True
            elif 'signin' not in current_url.lower() and 'amazon.com' in current_url:
                print("✅ Login successful! Not on signin page")
                return True
            elif 'ax/claim' in current_url and 'amazon.com' in current_url:
                print("✅ Login successful! Redirected to claim page")
                return True
            elif 'amazon.com' in current_url and 'signin' not in current_url.lower() and 'ap/signin' not in current_url.lower():
                print("✅ Login successful! On Amazon homepage")
                return True
            else:
                print("❌ Login failed - still on signin page or unexpected URL")
                return False
                
        except Exception as e:
            print(f"❌ Error checking login success: {e}")
            return False
    
    def logout(self):
        """Logout from Amazon to test full login flow"""
        print("\n📍 Logging out to test full login flow...")
        try:
            # Look for logout elements
            logout_selectors = [
                'a[href*="/ap/signout"]',
                'a:has-text("Sign Out")',
                'a:has-text("Sign out")',
                '#nav-item-signout',
                'a[data-nav-role="signout"]'
            ]
            
            # First try direct logout
            for selector in logout_selectors:
                try:
                    element = self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        self.page.click(selector)
                        time.sleep(0.5)
                        print("✅ Logged out successfully")
                        return True
                except:
                    continue
            
            # If no direct logout, try hovering over Account & Lists
            print("🔍 Trying Account & Lists hover...")
            account_selectors = [
                'a:has-text("Account & Lists")',
                '#nav-link-accountList',
                'a[data-nav-role="signin"]'
            ]
            
            for account_selector in account_selectors:
                try:
                    account_element = self.page.wait_for_selector(account_selector, timeout=3000)
                    if account_element:
                        account_element.hover()
                        time.sleep(1)
                        
                        # Look for logout in dropdown
                        signout_selectors = [
                            'a:has-text("Sign Out")',
                            'a:has-text("Sign out")',
                            'a[href*="/ap/signout"]',
                            '#nav-item-signout'
                        ]
                        
                        for signout_selector in signout_selectors:
                            try:
                                signout_element = self.page.wait_for_selector(signout_selector, timeout=2000)
                                if signout_element:
                                    self.page.click(signout_selector)
                                    time.sleep(0.5)
                                    print("✅ Logged out successfully via hover")
                                    return True
                            except:
                                continue
                        break
                except:
                    continue
            
            print("⚠️ Could not find logout button")
            return False
            
        except Exception as e:
            print(f"❌ Error during logout: {e}")
            return False
    
    def run_login_flow(self):
        """Run the complete login flow"""
        print("🔐 Starting Amazon Login Flow")
        print("=" * 50)
        
        try:
            # Start browser
            self.start_browser()
            
            # Step 1: Enter homepage
            if not self.step1_enter_homepage():
                return False
            
            # Step 2: Check for sign in
            has_signin, element, selector = self.step2_check_sign_in()
            
            if not has_signin:
                print("✅ User is already logged in!")
                return True
            
            # Step 3: Hover and click
            if not self.step3_hover_and_click(element, selector):
                return False
            
            # Step 4: Enter email
            if not self.step4_enter_email():
                return False
            
            # Step 5: Click continue
            if not self.step5_click_continue():
                return False
            
            # Step 6: Enter password
            if not self.step6_enter_password():
                return False
            
            # Step 7: Click sign in
            if not self.step7_click_sign_in():
                return False
            
            # Step 8: Check success
            success = self.step8_check_success()
            
            if success:
                print("\n🎉 Login flow completed successfully!")
            else:
                print("\n❌ Login flow failed!")
            
            return success
            
        except Exception as e:
            print(f"❌ Error in login flow: {e}")
            return False
        finally:
            # Keep browser open for inspection
            if not self.headless:
                try:
                    input("Press Enter to close browser...")
                except EOFError:
                    print("Non-interactive environment, closing browser...")
            self.close_browser()

def main():
    """Test the login component"""
    print("🧪 Testing Amazon Login Component")
    print("=" * 40)
    
    # Test with visible browser for debugging
    login_component = AmazonLoginComponent(headless=False)
    
    # First check if already logged in
    login_component.start_browser()
    login_component.step1_enter_homepage()
    has_signin, element, selector = login_component.step2_check_sign_in()
    
    if not has_signin:
        print("✅ User is already logged in! Testing logout first...")
        login_component.logout()
        print("Now testing full login flow...")
    
    success = login_component.run_login_flow()
    
    if success:
        print("✅ Login component test passed!")
    else:
        print("❌ Login component test failed!")

if __name__ == "__main__":
    main()
