#!/usr/bin/env python3
"""
Simple Amazon Review Search Component with working extraction logic
"""

from patchright.sync_api import sync_playwright
import time
import json
import os

class AmazonReviewSearchComponentSimple:
    def __init__(self, asin, product_url, headless=True, rating_filter=None, next_pages=0):
        """
        Initialize the review search component
        
        Args:
            asin (str): Amazon product ASIN
            product_url (str): Full product URL
            headless (bool): Run browser in headless mode
            rating_filter (int): Star rating to filter by (1, 2, 3, 4, 5, or None for all reviews)
            next_pages (int): Number of additional pages to scrape (0 = only current page)
        """
        self.asin = asin
        self.product_url = product_url
        self.headless = headless
        self.rating_filter = rating_filter
        self.next_pages = next_pages
        self.browser = None
        self.page = None
        self.reviews = []

    def start_browser(self):
        """Start the browser and create a new page"""
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

    def step1_navigate_to_product(self):
        """Step 1: Navigate directly to the product page"""
        print(f"\n📍 Step 1: Navigating directly to product page...")
        print(f"🔗 ASIN: {self.asin}")
        print(f"🔗 URL: {self.product_url}")
        
        try:
            self.page.goto(self.product_url, wait_until='domcontentloaded', timeout=15000)
            time.sleep(2)
            
            current_url = self.page.url
            page_title = self.page.title()
            
            print(f"✅ Navigated to: {current_url}")
            print(f"✅ Page title: {page_title}")
            
            # Verify we're on the correct product page
            if self.asin in current_url or self.asin in page_title:
                print(f"✅ Confirmed ASIN {self.asin} in URL/title")
                print(f"✅ Staying on product page: {current_url}")
                return True
            else:
                print(f"⚠️ ASIN {self.asin} not found in URL or title, but continuing...")
                return True
                
        except Exception as e:
            print(f"❌ Error navigating to product page: {e}")
            return False

    def step2_find_reviews_section(self):
        """Step 2: Find and navigate to the reviews section on the product page"""
        print(f"\n📍 Step 2: Finding reviews section on product page...")
        
        try:
            current_url = self.page.url
            if self.asin not in current_url:
                print(f"❌ Not on product page anymore. Current URL: {current_url}")
                return None
            
            print(f"✅ Still on product page: {current_url}")
            
            print("🔍 Scrolling down to find reviews section...")
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            time.sleep(2)
            
            review_selectors = [
                '#reviews-medley-footer',
                '[data-hook="reviews-medley-footer"]',
                'a[data-hook="see-all-reviews-link"]',
                'a[data-hook="reviews-medley-footer"]',
                'a:has-text("See all reviews")',
                'a:has-text("See more reviews")',
                '#reviews-medley-footer a',
                '.a-link-emphasis',
                'a[href*="#customerReviews"]',
                '.a-link-normal[href*="reviews"]'
            ]
            
            review_link = None
            for selector in review_selectors:
                try:
                    element = self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        text = element.text_content().strip()
                        href = element.get_attribute('href') or ''
                        print(f"🔍 Found review element: '{text}' using selector: {selector}")
                        print(f"🔗 Link: {href}")
                        
                        if (any(keyword in text.lower() for keyword in ['see more', 'see all', 'reviews', 'customer']) and 
                            ('amazon.com' in href or href.startswith('/') or '#customerReviews' in href)):
                            review_link = element
                            break
                except:
                    continue
            
            if review_link:
                print(f"✅ Found reviews section link")
                self.review_link = review_link
                return review_link
            else:
                print(f"❌ Could not find reviews section")
                return None
                
        except Exception as e:
            print(f"❌ Error finding reviews section: {e}")
            return None

    def step3_click_see_more_reviews(self, review_link):
        """Step 3: Click 'See more reviews' to navigate to the reviews page"""
        print(f"\n📍 Step 3: Clicking 'See more reviews'...")
        
        try:
            link_text = review_link.text_content().strip()
            link_href = review_link.get_attribute('href') or ''
            
            print(f"🔍 Clicking link: '{link_text}'")
            print(f"🔗 Link href: {link_href}")
            
            review_link.click()
            time.sleep(2)
            
            current_url = self.page.url
            page_title = self.page.title()
            
            print(f"✅ Clicked review link")
            print(f"✅ Current URL: {current_url}")
            print(f"✅ Page title: {page_title}")
            
            if 'product-reviews' in current_url and self.asin in current_url:
                print(f"✅ Successfully navigated to reviews page")
                return True
            else:
                print(f"⚠️ May not be on reviews page, but continuing...")
                return True
                
        except Exception as e:
            print(f"❌ Error clicking see more reviews: {e}")
            return False

    def step3_5_filter_by_rating(self):
        """Step 3.5: Filter reviews by star rating if specified"""
        if not self.rating_filter:
            print(f"\n📍 Step 3.5: No rating filter specified, continuing with all reviews...")
            return True
            
        print(f"\n📍 Step 3.5: Filtering reviews by {self.rating_filter} star rating...")
        
        try:
            # Map rating numbers to URL filter names
            rating_map = {
                5: 'five_star',
                4: 'four_star', 
                3: 'three_star',
                2: 'two_star',
                1: 'one_star'
            }
            
            filter_name = rating_map.get(self.rating_filter)
            if not filter_name:
                print(f"❌ Invalid rating filter: {self.rating_filter}")
                return True
            
            # Try multiple approaches to filter by star rating
            approaches = [
                # Approach 1: Direct URL construction
                {
                    'name': 'Direct URL construction',
                    'method': 'url'
                },
                # Approach 2: Click star chart link
                {
                    'name': 'Star chart link',
                    'method': 'chart'
                },
                # Approach 3: Click filter dropdown
                {
                    'name': 'Filter dropdown',
                    'method': 'dropdown'
                }
            ]
            
            for approach in approaches:
                print(f"\n🔍 Trying approach: {approach['name']}...")
                
                if approach['method'] == 'url':
                    # Direct URL construction
                    try:
                        current_url = self.page.url
                        base_url = current_url.split('?')[0]  # Remove existing query params
                        asin = self.asin
                        
                        # Construct filtered URL
                        filtered_url = f"{base_url}?ie=UTF8&reviewerType=all_reviews&filterByStar={filter_name}&pageNumber=1"
                        
                        print(f"🔗 Navigating to filtered URL: {filtered_url}")
                        self.page.goto(filtered_url, wait_until='domcontentloaded', timeout=15000)
                        time.sleep(2)
                        
                        new_url = self.page.url
                        print(f"✅ New URL: {new_url}")
                        
                        if filter_name in new_url:
                            print(f"✅ Successfully filtered to {self.rating_filter} star reviews using direct URL")
                            return True
                            
                    except Exception as e:
                        print(f"❌ Direct URL approach failed: {e}")
                        continue
                
                elif approach['method'] == 'chart':
                    # Click star chart approach
                    try:
                        star_selectors = [
                            f'a:has-text("{self.rating_filter} star")',
                            f'a[href*="{filter_name}"]',
                            f'a[href*="filterByStar"]'
                        ]
                        
                        star_element = None
                        for selector in star_selectors:
                            try:
                                element = self.page.wait_for_selector(selector, timeout=3000)
                                if element:
                                    href = element.get_attribute('href') or ''
                                    if filter_name in href or f'{self.rating_filter} star' in element.text_content():
                                        star_element = element
                                        break
                            except:
                                continue
                        
                        if star_element:
                            star_text = star_element.text_content().strip()
                            star_href = star_element.get_attribute('href') or ''
                            
                            print(f"🔍 Found {self.rating_filter} star chart link: '{star_text[:50]}...'")
                            print(f"🔗 Link: {star_href}")
                            
                            star_element.click()
                            time.sleep(2)
                            
                            current_url = self.page.url
                            print(f"✅ New URL after click: {current_url}")
                            
                            if filter_name in current_url:
                                print(f"✅ Successfully filtered to {self.rating_filter} star reviews using chart click")
                                return True
                            else:
                                print(f"⚠️ Chart click didn't change URL filter")
                                continue
                        else:
                            print(f"❌ Could not find {self.rating_filter} star chart element")
                            continue
                            
                    except Exception as e:
                        print(f"❌ Chart click approach failed: {e}")
                        continue
                
                elif approach['method'] == 'dropdown':
                    # Filter dropdown approach
                    try:
                        dropdown_selectors = [
                            'select[name="filterByStar"]',
                            '#filter-info-section select',
                            '.a-dropdown-container'
                        ]
                        
                        for selector in dropdown_selectors:
                            try:
                                dropdown = self.page.wait_for_selector(selector, timeout=3000)
                                if dropdown:
                                    print(f"🔍 Found dropdown using selector: {selector}")
                                    # Select the rating option
                                    dropdown.select_option(value=filter_name)
                                    time.sleep(2)
                                    
                                    current_url = self.page.url
                                    print(f"✅ New URL after dropdown: {current_url}")
                                    
                                    if filter_name in current_url:
                                        print(f"✅ Successfully filtered to {self.rating_filter} star reviews using dropdown")
                                        return True
                                    break
                            except:
                                continue
                        
                        print(f"❌ Could not find or use filter dropdown")
                        continue
                        
                    except Exception as e:
                        print(f"❌ Dropdown approach failed: {e}")
                        continue
            
            # If all approaches failed, warn but continue
            print(f"⚠️ All filtering approaches failed. Continuing with unfiltered reviews...")
            print(f"⚠️ Note: Extracted reviews may contain mixed ratings")
            return True
                
        except Exception as e:
            print(f"❌ Error in rating filter: {e}")
            return True

    def extract_reviews_from_page(self, page_number=1):
        """Extract detailed review data from a specific page"""
        print(f"\n    📊 Extracting review data from page {page_number}...")
        
        try:
            review_selector = '[data-hook="review"]'
            review_elements = self.page.query_selector_all(review_selector)
            
            if not review_elements:
                print(f"❌ No review elements found using selector: {review_selector}")
                return []
            
            print(f"✅ Found {len(review_elements)} review elements")
            
            # Extract review data using simple working JavaScript
            print("🔍 Executing JavaScript extraction...")
            try:
                reviews = self.page.evaluate('''() => {
                    const reviewElements = document.querySelectorAll('[data-hook="review"]');
                    const reviews = [];
                    
                    reviewElements.forEach((element, index) => {
                        try {
                            // Simple extraction using working selectors
                            const nameEl = element.querySelector('.a-profile-name');
                            const reviewerName = nameEl ? nameEl.textContent.trim() : '';
                            
                            const textEl = element.querySelector('[data-hook="review-body"]');
                            const reviewText = textEl ? textEl.textContent.trim() : '';
                            
                            // Extract rating
                            let rating = 0;
                            const ratingEl = element.querySelector('.a-icon-alt');
                            if (ratingEl) {
                                const ratingText = ratingEl.textContent || ratingEl.getAttribute('aria-label') || '';
                                const ratingMatch = ratingText.match(/(\\d+\\.?\\d*)\\s*out\\s*of\\s*5|(\\d+\\.?\\d*)\\s*stars?/);
                                if (ratingMatch) {
                                    const ratingValue = ratingMatch[1] || ratingMatch[2];
                                    rating = parseFloat(ratingValue);
                                }
                            }
                            
                            // Extract title
                            let reviewTitle = '';
                            const titleEl = element.querySelector('[data-hook="review-title"]');
                            if (titleEl) {
                                reviewTitle = titleEl.textContent.trim();
                                // Remove rating part and clean up newlines
                                reviewTitle = reviewTitle.replace(/\\d+\\.?\\d*\\s*out\\s*of\\s*5\\s*stars?[\\s\\n]*/gi, '');
                                reviewTitle = reviewTitle.replace(/\\n+/g, ' ').trim();
                            }
                            
                            // Extract location and date
                            let location = '';
                            let date = '';
                            const dateLocationEl = element.querySelector('[data-hook="review-date"]');
                            if (dateLocationEl) {
                                const dateLocationText = dateLocationEl.textContent.trim();
                                const fullMatch = dateLocationText.match(/Reviewed\\s+in\\s+([^\\s]+(?:\\s+[^\\s]+)*)\\s+on\\s+(.+)/i);
                                if (fullMatch) {
                                    location = fullMatch[1].trim();
                                    date = fullMatch[2].trim();
                                } else {
                                    const locationMatch = dateLocationText.match(/in\\s+([^\\s]+(?:\\s+[^\\s]+)*)/i);
                                    const dateMatch = dateLocationText.match(/on\\s+(.+)/i);
                                    if (locationMatch) location = locationMatch[1].trim();
                                    if (dateMatch) date = dateMatch[1].trim();
                                    if (!location && !date) date = dateLocationText;
                                }
                            }
                            
                            // Extract verified purchase
                            let verifiedPurchase = false;
                            const verifiedEl = element.querySelector('[data-hook="avp-badge"]');
                            if (verifiedEl) {
                                const verifiedText = verifiedEl.textContent.toLowerCase();
                                verifiedPurchase = verifiedText.includes('verified') || verifiedText.includes('purchase');
                            }
                            
                            // Note: helpfulVotes field removed per user request
                            
                            if (reviewerName && reviewText) {
                                reviews.push({
                                    reviewerName: reviewerName,
                                    rating: rating,
                                    title: reviewTitle,
                                    location: location,
                                    date: date,
                                    verifiedPurchase: verifiedPurchase,
                                    reviewText: reviewText,
                                    page: ''' + str(page_number) + '''
                                });
                            }
                        } catch (error) {
                            console.log('Error processing review element ' + index + ':', error);
                        }
                    });
                    
                    return reviews;
                }''')
                
                print(f"🔍 JavaScript execution completed. Reviews: {len(reviews) if reviews else 'None'}")
            except Exception as js_error:
                print(f"❌ JavaScript execution error: {js_error}")
                reviews = []
            
            if not reviews:
                print(f"❌ No reviews extracted from page {page_number}")
                return []
            
            print(f"✅ Extracted {len(reviews)} reviews from page {page_number}")
            
            return reviews
                
        except Exception as e:
            print(f"❌ Error extracting reviews from page {page_number}: {e}")
            return []

    def step4_extract_all_reviews(self):
        """Step 4: Extract reviews from all pages (current + additional pages)"""
        # Handle singular/plural grammar
        page_text = "page" if self.next_pages == 1 else "pages"
        print(f"\n📍 Step 4: Extracting reviews from {self.next_pages + 1} total {page_text} (current page + {self.next_pages} additional)...")
        
        all_reviews = []
        current_page = 1
        
        # Extract from current page (page 1)
        page_reviews = self.extract_reviews_from_page(current_page)
        if page_reviews:
            all_reviews.extend(page_reviews)
        
        # Navigate through additional pages
        for page_num in range(2, self.next_pages + 2):  # +2 because we want next_pages additional pages
            print(f"\n🔍 Looking for 'Next page' button...")
            
            # Look for next page button
            next_selectors = [
                '.a-pagination .a-last',
                'li.a-last a',
                'a[aria-label="Next page"]',
                '.a-pagination li:last-child a'
            ]
            
            next_button = None
            for selector in next_selectors:
                try:
                    button = self.page.wait_for_selector(selector, timeout=3000)
                    if button and not button.get_attribute('aria-disabled'):
                        next_button = button
                        break
                except:
                    continue
            
            if not next_button:
                print(f"❌ No more pages available. Stopped at page {current_page}")
                break
            
            print(f"✅ Found next page button using selector: {selector}")
            print(f"🔍 Clicking 'Next page' button to go to page {page_num}...")
            
            try:
                next_button.click()
                time.sleep(2)
                current_page = page_num
                
                # Extract reviews from this page
                page_reviews = self.extract_reviews_from_page(current_page)
                if page_reviews:
                    all_reviews.extend(page_reviews)
                else:
                    print(f"⚠️ No reviews found on page {current_page}")
                
            except Exception as e:
                print(f"❌ Error navigating to page {page_num}: {e}")
                break
        
        print(f"\n✅ Total reviews collected: {len(all_reviews)} across {current_page} pages")
        self.reviews = all_reviews
        return len(all_reviews) > 0

    def save_reviews_to_file(self, reviews):
        """Save reviews to JSON file"""
        try:
            # Create data directory if it doesn't exist
            data_dir = "data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
                print(f"📁 Created directory: {data_dir}")
            
            # Generate filename
            if self.rating_filter:
                filename = f"{data_dir}/reviews_{self.asin}_{self.rating_filter}.json"
            else:
                filename = f"{data_dir}/reviews_{self.asin}.json"
            
            # Save reviews to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(reviews, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved {len(reviews)} reviews to {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving reviews to file: {e}")
            return False

    def run_review_search_flow(self):
        """Run the complete review search flow"""
        print("🔍 Starting Amazon Review Search Flow")
        print("=" * 50)
        print(f"ASIN: {self.asin}")
        print(f"Product URL: {self.product_url}")
        print("=" * 50)
        
        try:
            # Start browser only if not already provided
            if not self.browser or not self.page:
                self.start_browser()
            
            # Step 1: Navigate to product page
            if not self.step1_navigate_to_product():
                print("❌ Failed to navigate to product page")
                return False
            
            # Step 2: Find reviews section
            review_link = self.step2_find_reviews_section()
            if not review_link:
                print("❌ Failed to find reviews section")
                return False
            
            # Step 3: Click see more reviews
            if not self.step3_click_see_more_reviews(review_link):
                print("❌ Failed to click see more reviews")
                return False
            
            # Step 3.5: Filter by rating if specified
            if not self.step3_5_filter_by_rating():
                print("❌ Failed to filter by rating")
                return False
            
            # Step 4: Extract reviews (with pagination if specified)
            if self.next_pages > 0:
                if not self.step4_extract_all_reviews():
                    print("❌ Failed to extract reviews with pagination")
                    return False
            else:
                page_reviews = self.extract_reviews_from_page()
                if not page_reviews:
                    print("❌ Failed to extract reviews")
                    return False
                self.reviews = page_reviews
            
            # Save reviews to file
            if not self.save_reviews_to_file(self.reviews):
                print("❌ Failed to save reviews to file")
                return False
            
            print("\n🎉 Review search flow completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error in review search flow: {e}")
            return False
        
        finally:
            # Keep browser open for inspection
            try:
                input("Press Enter to close browser...")
            except EOFError:
                print("Non-interactive environment, closing browser...")
            self.close_browser()

if __name__ == "__main__":
    # Test the component
    component = AmazonReviewSearchComponentSimple(
        asin="B0C7C69FPS",
        product_url="https://www.amazon.com/eufy-Security-Fingerprint-Deadbolt-Waterproof/dp/B0C7C69FPS/ref=sr_1_5?crid=1DASSKGSZRWX&dib=eyJ2IjoiMSJ9.OEGtUl2GtKYYsWXjHrbAzJDlKcDZ_QHxGiujtAqJB17mxMYRO3CMue9NIO5aJTTmobLYmZx7JU8AA3POyVr2Ref-RuPEEUaAGxabPb6V-KWFB4HNdLPGvkzxNnoSbo3934DWXuiB_EAQpyf-yNbweRjqg7bsRNy_1wzTVpM2W8Nd8jbWzxIoblN8F3vLMws1I3HLjyACQGPOYLuB38wzkLSkRe4LGE7vtjbnwMjwTUEbwmz3sThzDZuWKnS-d9zPUD24lD5UUDsXrKDLO_0-9iiCVogu48aDTrKVw6b4cRk.cLtIxgy7ujn5mjHjr2XFpCTUx0EwcQ9fsESqQ1LxpFc&dib_tag=se&keywords=smart+lock&qid=1758094999&sprefix=%2Caps%2C54&sr=8-5",
        headless=False,
        rating_filter=5,
        next_pages=0
    )
    component.run_review_search_flow()
