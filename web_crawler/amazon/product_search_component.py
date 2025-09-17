#!/usr/bin/env python3
"""
Amazon Product Search Component
Searches for products and extracts product information
"""

from patchright.sync_api import sync_playwright
import time
import json
import os

class AmazonProductSearchComponent:
    def __init__(self, product_name, max_products=5, headless=False):
        self.product_name = product_name
        self.max_products = max_products
        self.headless = headless
        self.browser = None
        self.page = None
        self.products = []
    
    def start_browser(self):
        """Start the browser"""
        print("🚀 Starting browser...")
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        print("✅ Browser started")
    
    def close_browser(self):
        """Close the browser"""
        if self.browser:
            self.browser.close()
            print("🔒 Browser closed")
    
    def step1_navigate_to_amazon(self):
        """Step 1: Navigate to Amazon homepage"""
        print(f"\n📍 Step 1: Navigating to Amazon homepage...")
        try:
            self.page.goto('https://www.amazon.com/', wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)
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
                        time.sleep(3)
                        print(f"✅ Clicked continue shopping, current URL: {self.page.url}")
                        break
                except:
                    continue
            
            return True
        except Exception as e:
            print(f"❌ Error navigating to Amazon: {e}")
            return False
    
    def step2_enter_search_term(self):
        """Step 2: Enter search term in search box"""
        print(f"\n📍 Step 2: Entering search term: '{self.product_name}'...")
        try:
            # Find search box
            search_selectors = [
                '#twotabsearchtextbox',
                'input[name="field-keywords"]',
                'input[placeholder*="Search"]',
                'input[aria-label*="Search"]'
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = self.page.wait_for_selector(selector, timeout=5000)
                    if search_box:
                        print(f"✅ Found search box using selector: {selector}")
                        break
                except:
                    continue
            
            if not search_box:
                print("❌ Could not find search box")
                return False
            
            # Clear and enter search term (fill automatically clears)
            search_box.fill(self.product_name)
            print(f"✅ Entered search term: '{self.product_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Error entering search term: {e}")
            return False
    
    def step3_click_search(self):
        """Step 3: Click search button"""
        print(f"\n📍 Step 3: Clicking search button...")
        try:
            # Find search button
            search_button_selectors = [
                '#nav-search-submit-button',
                'input[type="submit"][value="Go"]',
                'button[type="submit"]',
                '.nav-search-submit'
            ]
            
            for selector in search_button_selectors:
                try:
                    search_button = self.page.wait_for_selector(selector, timeout=5000)
                    if search_button:
                        print(f"✅ Found search button using selector: {selector}")
                        self.page.click(selector)
                        time.sleep(5)  # Wait for search results to load
                        print(f"✅ Clicked search, current URL: {self.page.url}")
                        return True
                except:
                    continue
            
            # If no search button found, try pressing Enter
            print("⚠️ No search button found, trying Enter key")
            self.page.keyboard.press('Enter')
            time.sleep(5)
            print(f"✅ Pressed Enter, current URL: {self.page.url}")
            return True
            
        except Exception as e:
            print(f"❌ Error clicking search: {e}")
            return False
    
    def step4_wait_for_results(self):
        """Step 4: Wait for search results to load"""
        print(f"\n📍 Step 4: Waiting for search results...")
        try:
            # Wait for search results to be visible
            result_selectors = [
                '[data-component-type="s-search-result"]',
                '[data-component-type="s-product-image"]',
                '.s-result-item',
                '[data-asin]'
            ]
            
            for selector in result_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=10000)
                    print(f"✅ Search results loaded using selector: {selector}")
                    return True
                except:
                    continue
            
            print("⚠️ Search results not found, proceeding anyway...")
            return True
            
        except Exception as e:
            print(f"❌ Error waiting for results: {e}")
            return False
    
    def step5_extract_products(self):
        """Step 5: Extract product information"""
        print(f"\n📍 Step 5: Extracting top {self.max_products} products...")
        try:
            # Extract products using JavaScript
            products = self.page.evaluate(f'''() => {{
                const products = [];
                // Use the most reliable selector for search results
                const productElements = document.querySelectorAll('[data-component-type="s-search-result"]');
                console.log('Found product elements:', productElements.length);
                
                // Process more elements to find enough valid products
                for (let i = 0; i < Math.min({self.max_products * 3}, productElements.length); i++) {{
                    const element = productElements[i];
                    
                    // Extract title - try multiple approaches
                    let title = '';
                    
                    // First try the most common selectors
                    const titleSelectors = [
                        'h2 a span',
                        'h2 span',
                        '.a-size-base-plus span',
                        '.a-color-base.a-text-normal',
                        'h2',
                        '.a-size-base-plus',
                        'span[data-component-type="s-product-image"]',
                        '.s-size-mini'
                    ];
                    
                    for (const selector of titleSelectors) {{
                        const titleEl = element.querySelector(selector);
                        if (titleEl) {{
                            title = titleEl.textContent.trim();
                            // Clean up the title
                            title = title.replace(/\\s+/g, ' ').trim();
                            if (title && title.length > 10) {{
                                break;
                            }}
                        }}
                    }}
                    
                    // If no title found, try getting it from the link's title attribute
                    if (!title) {{
                        const linkEl = element.querySelector('a[href*="/dp/"]');
                        if (linkEl) {{
                            title = linkEl.getAttribute('title') || linkEl.textContent.trim();
                            title = title.replace(/\\s+/g, ' ').trim();
                        }}
                    }}
                    
                    // Extract ASIN
                    let asin = '';
                    const asinSelectors = ['a[href*="/dp/"]', 'h2 a'];
                    for (const selector of asinSelectors) {{
                        const linkEl = element.querySelector(selector);
                        if (linkEl && linkEl.href) {{
                            const asinMatch = linkEl.href.match(/\\/dp\\/([A-Z0-9]{{10}})/);
                            if (asinMatch) {{
                                asin = asinMatch[1];
                                break;
                            }}
                        }}
                    }}
                    
                    // Extract price
                    let price = 0;
                    const priceSelectors = [
                        '.a-price-whole',
                        '.a-price .a-offscreen',
                        '.a-price-range',
                        '.a-price-symbol + .a-price-whole',
                        '[data-a-price]'
                    ];
                    
                    for (const selector of priceSelectors) {{
                        const priceEl = element.querySelector(selector);
                        if (priceEl) {{
                            let priceText = priceEl.textContent.trim();
                            // Try to get the full price including decimal
                            if (selector === '.a-price-whole') {{
                                const priceFraction = element.querySelector('.a-price-fraction');
                                if (priceFraction) {{
                                    priceText += '.' + priceFraction.textContent.trim();
                                }}
                            }}
                            // Clean up the price text
                            priceText = priceText.replace(/[^\\d.,]/g, '');
                            // Fix double dots
                            priceText = priceText.replace(/\\.\\./g, '.');
                            if (priceText) {{
                                price = parseFloat(priceText.replace(/,/g, ''));
                                break;
                            }}
                        }}
                    }}
                    
                    // Extract rating
                    let rating = 0;
                    const ratingSelectors = [
                        '.a-icon-alt',
                        '[data-hook="rating-out-of-text"]',
                        '.a-icon-star',
                        '.a-star-mini'
                    ];
                    
                    for (const selector of ratingSelectors) {{
                        const ratingEl = element.querySelector(selector);
                        if (ratingEl) {{
                            const ratingText = ratingEl.textContent || ratingEl.getAttribute('aria-label') || '';
                            const ratingMatch = ratingText.match(/(\\d+\\.?\\d*)\\s*out\\s*of\\s*5|(\\d+\\.?\\d*)\\s*stars?/);
                            if (ratingMatch) {{
                                const ratingValue = ratingMatch[1] || ratingMatch[2];
                                // Validate that it's a reasonable rating (1-5)
                                if (ratingValue && parseFloat(ratingValue) >= 1 && parseFloat(ratingValue) <= 5) {{
                                    rating = parseFloat(ratingValue);
                                    break;
                                }}
                            }}
                        }}
                    }}
                    
                    // Extract review count - look for hyperlink with review count
                    let reviewCount = 0;
                    
                    // First try to find links that contain review count
                    const reviewLinkSelectors = [
                        'a[href*="#customerReviews"]',
                        'a[href*="reviews"]',
                        'a[href*="rating"]',
                        'a:has-text("reviews")',
                        'a:has-text("rating")'
                    ];
                    
                    for (const selector of reviewLinkSelectors) {{
                        const reviewLink = element.querySelector(selector);
                        if (reviewLink) {{
                            const linkText = reviewLink.textContent.trim();
                            // Look for numbers in the link text
                            const match = linkText.match(/([\\d,]+)/);
                            if (match) {{
                                const num = match[1];
                                // Make sure it's a reasonable review count
                                const reviewNum = parseInt(num.replace(/,/g, ''));
                                if (reviewNum > 0 && reviewNum < 100000) {{
                                    reviewCount = reviewNum;
                                    break;
                                }}
                            }}
                        }}
                    }}
                    
                    // If not found in links, try looking for text patterns
                    if (reviewCount === 0) {{
                        const elementText = element.textContent || '';
                        const patterns = [
                            /(\\d+)\\s*reviews?/i,
                            /(\\d+)\\s*ratings?/i
                        ];
                        
                        for (const pattern of patterns) {{
                            const match = elementText.match(pattern);
                            if (match) {{
                                const num = match[1];
                                // Make sure it's a reasonable review count (not a price or other number)
                                const reviewNum = parseInt(num);
                                if (reviewNum > 0 && reviewNum < 100000) {{
                                    reviewCount = reviewNum;
                                    break;
                                }}
                            }}
                        }}
                    }}
                    
                    // If still not found, try other common selectors
                    if (reviewCount === 0) {{
                        const reviewSelectors = [
                            '[data-hook="total-review-count"]',
                            '.a-link-normal',
                            '.a-size-base',
                            '.a-size-small'
                        ];
                        
                        for (const selector of reviewSelectors) {{
                            const reviewEl = element.querySelector(selector);
                            if (reviewEl) {{
                                const reviewText = reviewEl.textContent || reviewEl.getAttribute('aria-label') || '';
                                const patterns = [
                                    /([\\d,]+)\\s*reviews?/i,
                                    /([\\d,]+)\\s*ratings?/i,
                                    /([\\d,]+)/i
                                ];
                                
                                for (const pattern of patterns) {{
                                    const match = reviewText.match(pattern);
                                    if (match && (reviewText.toLowerCase().includes('review') || reviewText.toLowerCase().includes('rating'))) {{
                                        const reviewNum = parseInt(match[1].replace(/,/g, ''));
                                        if (reviewNum > 0 && reviewNum < 100000) {{
                                            reviewCount = reviewNum;
                                            break;
                                        }}
                                    }}
                                }}
                                if (reviewCount > 0) break;
                            }}
                        }}
                    }}
                    
                    // Extract URL
                    let url = '';
                    const urlSelectors = [
                        'h2 a',
                        'a[href*="/dp/"]',
                        '.a-link-normal',
                        'a[data-asin]'
                    ];
                    
                    for (const selector of urlSelectors) {{
                        const linkEl = element.querySelector(selector);
                        if (linkEl && linkEl.href) {{
                            url = linkEl.href;
                            // Make sure it's a full URL
                            if (url.startsWith('/')) {{
                                url = 'https://www.amazon.com' + url;
                            }}
                            break;
                        }}
                    }}
                    
                    // Only require title and ASIN, other fields can be empty
                    if (title && asin) {{
                        products.push({{
                            rank: products.length + 1,
                            title: title,
                            asin: asin,
                            price: price || 0,
                            rating: rating || 0,
                            reviewCount: reviewCount || 0,
                            url: url || ''
                        }});
                        console.log('Added product ' + products.length + ': ' + title.substring(0, 50) + '...');
                        
                        // Stop if we have enough products
                        if (products.length >= {self.max_products}) {{
                            console.log('Found enough products, stopping at element ' + i);
                            break;
                        }}
                    }} else {{
                        // Debug: log what we found
                        console.log('Element ' + i + ': title="' + title + '", asin="' + asin + '"');
                    }}
                }}
                
                return products;
            }}''')
            
            self.products = products
            print(f"✅ Extracted {len(products)} products")
            
            if len(products) == 0:
                print("⚠️ No products extracted, checking page content...")
                # Debug: Check what's on the page
                page_title = self.page.title()
                current_url = self.page.url
                print(f"Page title: {page_title}")
                print(f"Current URL: {current_url}")
                
                # Check for any product-like elements
                all_elements = self.page.query_selector_all('[data-component-type]')
                print(f"Found {len(all_elements)} elements with data-component-type")
                for i, elem in enumerate(all_elements[:5]):  # Show first 5
                    component_type = elem.get_attribute('data-component-type')
                    print(f"  Element {i+1}: {component_type}")
            
            # Print product summary
            for product in products:
                print(f"  {product['rank']}. {product['title'][:60]}...")
                print(f"     ASIN: {product['asin']}, Price: {product['price']}, Rating: {product['rating']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error extracting products: {e}")
            return False
    
    def step6_save_to_json(self):
        """Step 6: Save products to JSON file"""
        print(f"\n📍 Step 6: Saving products to JSON file...")
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Create filename
            filename = f"data/products_{self.product_name.replace(' ', '_')}.json"
            
            # Save to JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved {len(self.products)} products to {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving to JSON: {e}")
            return False
    
    def run_search_flow(self):
        """Run the complete product search flow"""
        print(f"🔍 Starting Amazon Product Search Flow")
        print(f"Product: {self.product_name}")
        print(f"Max products: {self.max_products}")
        print("=" * 50)
        
        try:
            # Start browser
            self.start_browser()
            
            # Step 1: Navigate to Amazon homepage
            if not self.step1_navigate_to_amazon():
                return False
            
            # Step 2: Enter search term in search bar
            if not self.step2_enter_search_term():
                return False
            
            # Step 3: Click search button
            if not self.step3_click_search():
                return False
            
            # Step 4: Wait for search results to load
            if not self.step4_wait_for_results():
                return False
            
            # Step 5: Extract products from search results
            if not self.step5_extract_products():
                return False
            
            # Step 6: Save products to JSON file
            if not self.step6_save_to_json():
                return False
            
            print("\n🎉 Product search flow completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error in search flow: {e}")
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
    """Test the product search component"""
    print("🧪 Testing Amazon Product Search Component")
    print("=" * 50)
    
    # Test parameters
    product_name = "smart lock"
    max_products = 5
    
    # Test with visible browser for debugging
    search_component = AmazonProductSearchComponent(
        product_name=product_name,
        max_products=max_products,
        headless=False
    )
    
    success = search_component.run_search_flow()
    
    if success:
        print("✅ Product search component test passed!")
    else:
        print("❌ Product search component test failed!")

if __name__ == "__main__":
    main()
