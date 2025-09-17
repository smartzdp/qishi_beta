#!/usr/bin/env python3
"""
Final Complete Amazon Workflow - Robust version:
1. Login once and stay logged in
2. Search products using search bar directly 
3. Extract multiple products with improved selectors
4. Review search for ALL products with proper browser management
"""

import json
import os
import time
import re

def final_complete_workflow(search_term="smart lock", max_products=3, rating_filter=5, next_pages=1):
    """
    Final complete workflow with robust product extraction and review search
    
    Args:
        search_term (str): Product to search for
        max_products (int): Number of top products to extract
        rating_filter (int): Star rating to filter reviews (1-5)
        next_pages (int): Number of additional pages to scrape for reviews
    """
    
    print("🚀 Final Complete Amazon Workflow")
    print("=" * 60)
    print(f"📝 Search Term: {search_term}")
    print(f"📊 Max Products: {max_products}")
    print(f"⭐ Rating Filter: {rating_filter} stars")
    print(f"📄 Additional Pages: {next_pages}")
    print("=" * 60)
    
    try:
        # Step 1: Login
        print("\n🔐 Step 1: Logging into Amazon...")
        from login_component import AmazonLoginComponent
        
        login_component = AmazonLoginComponent(headless=False)
        login_component.start_browser()
        
        # Manual login steps
        if not login_component.step1_enter_homepage():
            print("❌ Failed to enter homepage")
            return False
        
        sign_in_found, sign_in_element, sign_in_selector = login_component.step2_check_sign_in()
        if not sign_in_found:
            print("✅ Already logged in, logging out first...")
            login_component.logout()
            time.sleep(2)
            # Re-check after logout
            sign_in_found, sign_in_element, sign_in_selector = login_component.step2_check_sign_in()
        
        if not login_component.step3_hover_and_click(sign_in_element, sign_in_selector):
            print("❌ Failed to hover and click sign in")
            return False
        
        if not login_component.step4_enter_email():
            print("❌ Failed to enter email")
            return False
        
        if not login_component.step5_click_continue():
            print("❌ Failed to click continue")
            return False
        
        if not login_component.step6_enter_password():
            print("❌ Failed to enter password")
            return False
        
        if not login_component.step7_click_sign_in():
            print("❌ Failed to click sign in")
            return False
        
        if not login_component.step8_check_success():
            print("❌ Login failed")
            return False
        
        print("✅ Login successful!")
        
        # Step 2: Product Search using search bar (IMPROVED)
        print(f"\n🔍 Step 2: Searching for '{search_term}' using search bar...")
        
        page = login_component.page
        
        # Navigate to Amazon homepage if not already there
        current_url = page.url
        if "amazon.com" not in current_url or "/ap/" in current_url or "/claim" in current_url:
            print("🏠 Navigating to Amazon homepage...")
            page.goto("https://www.amazon.com", wait_until='domcontentloaded', timeout=15000)
            time.sleep(2)
        
        # Find and use search box directly
        print("🔍 Finding search box...")
        search_box = page.wait_for_selector('#twotabsearchtextbox', timeout=10000)
        
        # Clear and enter search term
        search_box.fill(search_term)
        print(f"✅ Entered search term: '{search_term}'")
        
        # Click search button
        search_button = page.wait_for_selector('#nav-search-submit-button', timeout=5000)
        search_button.click()
        
        # Wait for results
        page.wait_for_selector('[data-component-type="s-search-result"]', timeout=10000)
        time.sleep(3)
        print(f"✅ Search results loaded")
        
        # Step 3: Extract Products with IMPROVED selectors
        print(f"🔍 Step 3: Extracting top {max_products} products...")
        
        products = []
        product_elements = page.query_selector_all('[data-component-type="s-search-result"]')
        
        print(f"🔍 Found {len(product_elements)} product elements")
        
        for i, element in enumerate(product_elements):
            if len(products) >= max_products:
                break
                
            try:
                print(f"\n   🔍 Processing element {i+1}...")
                
                # Extract product name with multiple strategies
                name = ""
                name_strategies = [
                    lambda el: el.query_selector('h2 a span'),
                    lambda el: el.query_selector('h2 span'),
                    lambda el: el.query_selector('.a-size-mini span'),
                    lambda el: el.query_selector('.a-size-base-plus'),
                    lambda el: el.query_selector('[data-cy="title-recipe-title"]'),
                    lambda el: el.query_selector('.s-size-mini span')
                ]
                
                for strategy in name_strategies:
                    try:
                        name_el = strategy(element)
                        if name_el:
                            candidate_name = name_el.text_content().strip()
                            if candidate_name and len(candidate_name) > 10 and not candidate_name.startswith('$'):
                                name = candidate_name
                                print(f"      ✅ Name: {name[:50]}...")
                                break
                    except:
                        continue
                
                if not name:
                    print(f"      ❌ No valid name found")
                    continue
                
                # Extract ASIN and URL from link with multiple strategies
                url = ""
                asin = ""
                link_strategies = [
                    lambda el: el.query_selector('h2 a'),
                    lambda el: el.query_selector('.a-link-normal'),
                    lambda el: el.query_selector('a[href*="/dp/"]')
                ]
                
                for strategy in link_strategies:
                    try:
                        link_el = strategy(element)
                        if link_el:
                            href = link_el.get_attribute('href')
                            if href and '/dp/' in href:
                                url = f"https://www.amazon.com{href}" if href.startswith('/') else href
                                # Extract ASIN from URL
                                asin_match = re.search(r'/dp/([A-Z0-9]{10})', href)
                                if asin_match:
                                    asin = asin_match.group(1)
                                    print(f"      ✅ ASIN: {asin}")
                                    print(f"      ✅ URL: {url[:80]}...")
                                    break
                    except:
                        continue
                
                if not asin or not url:
                    print(f"      ❌ No valid ASIN/URL found")
                    continue
                
                # Extract price with improved decimal handling
                price = "N/A"
                try:
                    # First try to get whole price with fraction
                    price_whole_el = element.query_selector('.a-price-whole')
                    if price_whole_el:
                        price_text = price_whole_el.text_content().strip()
                        # Look for fraction part
                        price_fraction_el = element.query_selector('.a-price-fraction')
                        if price_fraction_el:
                            fraction_text = price_fraction_el.text_content().strip()
                            price_text = f"{price_text}.{fraction_text}"
                        
                        # Clean and validate
                        if price_text:
                            # Fix double dots issue (e.g., "39..99" -> "39.99")
                            price_text = price_text.replace('..', '.')
                            # Convert to number
                            try:
                                price = float(price_text)
                                print(f"      ✅ Price: ${price}")
                            except ValueError:
                                price = "N/A"
                                print(f"      ⚠️ Could not parse price: {price_text}")
                        else:
                            price = "N/A"
                    
                    # Fallback strategies if whole+fraction didn't work
                    if price == "N/A":
                        price_strategies = [
                            lambda el: el.query_selector('.a-offscreen'),
                            lambda el: el.query_selector('.a-price .a-offscreen'),
                            lambda el: el.query_selector('.a-price-range .a-offscreen')
                        ]
                        
                        for strategy in price_strategies:
                            try:
                                price_el = strategy(element)
                                if price_el:
                                    price_text = price_el.text_content().strip()
                                    if price_text and ('$' in price_text or '.' in price_text):
                                        # Clean price text and convert to number
                                        clean_price = price_text.replace('$', '').replace(',', '')
                                        try:
                                            price = float(clean_price)
                                            print(f"      ✅ Price: ${price}")
                                            break
                                        except ValueError:
                                            continue
                            except:
                                continue
                except Exception as e:
                    print(f"      ⚠️ Price extraction error: {e}")
                    pass
                
                # Extract rating with multiple strategies
                rating = "N/A"
                rating_strategies = [
                    lambda el: el.query_selector('.a-icon-alt'),
                    lambda el: el.query_selector('[aria-label*="stars"]'),
                    lambda el: el.query_selector('.a-star-mini .a-icon-alt')
                ]
                
                for strategy in rating_strategies:
                    try:
                        rating_el = strategy(element)
                        if rating_el:
                            rating_text = rating_el.text_content() or rating_el.get_attribute('aria-label') or ''
                            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                            if rating_match:
                                try:
                                    rating_val = float(rating_match.group(1))
                                    if 1 <= rating_val <= 5:  # Valid rating range
                                        rating = rating_val
                                        print(f"      ✅ Rating: {rating}")
                                        break
                                except:
                                    continue
                    except:
                        continue
                
                # Extract review count with improved K/M suffix handling
                review_count = "N/A"
                review_strategies = [
                    lambda el: el.query_selector('a[href*="#customerReviews"]'),
                    lambda el: el.query_selector('.a-size-base'),
                    lambda el: el.query_selector('span[aria-label*="stars"]'),
                    lambda el: el.query_selector('.a-link-normal[href*="reviews"]')
                ]
                
                for strategy in review_strategies:
                    try:
                        review_el = strategy(element)
                        if review_el:
                            review_text = review_el.text_content()
                            if review_text:
                                # Look for patterns like "34.8K", "1.2M", "1,234", etc.
                                review_patterns = [
                                    r'([\d,]+\.?\d*[KMkm])',  # 34.8K, 1.2M
                                    r'([\d,]+)',              # 1,234
                                ]
                                
                                for pattern in review_patterns:
                                    review_matches = re.findall(pattern, review_text)
                                    for match in review_matches:
                                        if match:
                                            review_count = match
                                            print(f"      ✅ Review Count: {review_count}")
                                            break
                                    if review_count != "N/A":
                                        break
                                if review_count != "N/A":
                                    break
                    except:
                        continue
                
                # Add valid product
                product = {
                    'rank': len(products) + 1,
                    'name': name,
                    'asin': asin,
                    'url': url,
                    'price': price,
                    'rating': rating,
                    'review_count': review_count
                }
                products.append(product)
                print(f"      ✅ Added product #{len(products)}: {name[:40]}...")
                
            except Exception as e:
                print(f"      ❌ Error processing element {i+1}: {e}")
                continue
        
        print(f"\n✅ Successfully extracted {len(products)} products")
        
        if len(products) == 0:
            print("❌ No products extracted. Cannot continue with review search.")
            login_component.close_browser()
            return False
        
        # Save products to JSON
        os.makedirs("data", exist_ok=True)
        products_file = f"data/products_{search_term.replace(' ', '_')}_final.json"
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved products to {products_file}")
        
        # Step 4: Review Search for ALL products (FIXED browser management)
        print(f"\n📝 Step 4: Extracting reviews for ALL products...")
        from review_search_component_simple import AmazonReviewSearchComponentSimple
        
        review_results = []
        
        for i, product in enumerate(products, 1):
            print(f"\n📍 Processing Product {i}/{len(products)}: {product['name'][:40]}...")
            print(f"   ⭐ Star Filter: {rating_filter} stars")
            print(f"   📄 Pages: {next_pages + 1} total")
            
            try:
                # Create review search component
                review_component = AmazonReviewSearchComponentSimple(
                    asin=product['asin'],
                    product_url=product['url'],
                    headless=False,
                    rating_filter=rating_filter,
                    next_pages=next_pages
                )
                
                # Use the SAME browser instance (CRITICAL FIX)
                review_component.browser = login_component.browser
                review_component.page = login_component.page
                
                # IMPORTANT: Don't let the component close the browser
                original_close_method = review_component.close_browser
                review_component.close_browser = lambda: print("   🔒 Skipping browser close (keeping for next product)")
                
                # Run review search
                if review_component.run_review_search_flow():
                    review_count = len(review_component.reviews)
                    print(f"   ✅ Extracted {review_count} reviews ({rating_filter}-star)")
                    
                    review_results.append({
                        'product_name': product['name'],
                        'asin': product['asin'],
                        'star_rating': rating_filter,
                        'review_count': review_count,
                        'filename': f"reviews_{product['asin']}_{rating_filter}.json",
                        'status': 'success'
                    })
                else:
                    print(f"   ❌ Failed to extract reviews")
                    review_results.append({
                        'product_name': product['name'],
                        'asin': product['asin'],
                        'star_rating': rating_filter,
                        'review_count': 0,
                        'filename': None,
                        'status': 'failed'
                    })
                
                # Restore original close method
                review_component.close_browser = original_close_method
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                review_results.append({
                    'product_name': product['name'],
                    'asin': product['asin'],
                    'star_rating': rating_filter,
                    'review_count': 0,
                    'filename': None,
                    'status': 'error',
                    'error': str(e)
                })
                
                # Continue with next product even if one fails
                continue
        
        # Final Summary
        print("\n" + "=" * 60)
        print("🎉 FINAL WORKFLOW COMPLETED!")
        print("=" * 60)
        
        total_reviews = sum(r['review_count'] for r in review_results)
        successful_products = sum(1 for r in review_results if r['review_count'] > 0)
        
        print(f"\n📊 Final Summary:")
        print(f"   Search Term: '{search_term}'")
        print(f"   Products Found: {len(products)}")
        print(f"   Successful Review Extractions: {successful_products}/{len(products)}")
        print(f"   Total Reviews Extracted: {total_reviews}")
        print(f"   Star Filter: {rating_filter} stars")
        print(f"   Pages per Product: {next_pages + 1}")
        
        print(f"\n📄 Detailed Results:")
        for i, (product, result) in enumerate(zip(products, review_results), 1):
            status = "✅" if result['review_count'] > 0 else "❌"
            print(f"   {i}. {status} {product['name'][:40]}...")
            print(f"      ASIN: {product['asin']} | Rating: {product.get('rating', 'N/A')} | Price: {product.get('price', 'N/A')}")
            print(f"      Reviews Extracted: {result['review_count']} ({rating_filter}-star)")
            if result['filename']:
                print(f"      File: data/{result['filename']}")
        
        print(f"\n📁 Generated Files:")
        print(f"   • {products_file}")
        for result in review_results:
            if result['filename']:
                print(f"   • data/{result['filename']}")
        
        # Close browser only at the very end
        print(f"\n🔒 Closing browser...")
        login_component.close_browser()
        
        return True
        
    except Exception as e:
        print(f"❌ Error in final workflow: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to close browser
        try:
            if 'login_component' in locals():
                login_component.close_browser()
        except:
            pass
        
        return False

if __name__ == "__main__":
    # Test the final workflow
    success = final_complete_workflow(
        search_term="smart lock",
        max_products=3,
        rating_filter=4,  # 4-star reviews this time
        next_pages=1      # 2 total pages (1 base + 1 additional)
    )
    
    if success:
        print("\n🎉 Final workflow completed successfully!")
    else:
        print("\n❌ Final workflow failed!")
