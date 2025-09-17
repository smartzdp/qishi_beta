#!/usr/bin/env python3
"""
Interactive Amazon Scraper
Prompts user for search parameters and runs the complete workflow
"""

import sys
from final_complete_workflow import final_complete_workflow

def get_user_input():
    """Get user input for scraping parameters"""
    
    print("🚀 Interactive Amazon Scraper")
    print("=" * 50)
    print("Configure your scraping parameters:")
    print()
    
    # Product name
    product_name = input("📝 Product name (default: smart lock): ").strip()
    if not product_name:
        product_name = "smart lock"
    
    # Product number
    while True:
        product_num_input = input("📊 Number of products (default: 3): ").strip()
        if not product_num_input:
            product_num = 3
            break
        try:
            product_num = int(product_num_input)
            if product_num < 1 or product_num > 10:
                print("⚠️  Please enter a number between 1 and 10")
                continue
            break
        except ValueError:
            print("⚠️  Please enter a valid number")
    
    # Review rating filter
    while True:
        rating_input = input("⭐ Review rating filter (1-5, or press Enter for none): ").strip()
        if not rating_input:
            rating_filter = None
            break
        try:
            rating_filter = int(rating_input)
            if rating_filter < 1 or rating_filter > 5:
                print("⚠️  Please enter a rating between 1 and 5, or press Enter for none")
                continue
            break
        except ValueError:
            print("⚠️  Please enter a valid rating (1-5) or press Enter for none")
    
    # Review next pages
    while True:
        pages_input = input("📄 Additional review pages (default: 1): ").strip()
        if not pages_input:
            next_pages = 1
            break
        try:
            next_pages = int(pages_input)
            if next_pages < 0 or next_pages > 5:
                print("⚠️  Please enter a number between 0 and 5")
                continue
            break
        except ValueError:
            print("⚠️  Please enter a valid number")
    
    return product_name, product_num, rating_filter, next_pages

def display_summary(product_name, product_num, rating_filter, next_pages):
    """Display the configuration summary"""
    
    print("\n" + "=" * 50)
    print("📋 Configuration Summary:")
    print(f"   Product: {product_name}")
    print(f"   Number of products: {product_num}")
    print(f"   Rating filter: {rating_filter if rating_filter else 'None (all ratings)'}")
    print(f"   Total pages per product: {next_pages + 1} ({next_pages} additional)")
    print("=" * 50)
    
    # Confirm before proceeding
    confirm = input("\n✅ Proceed with scraping? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Scraping cancelled.")
        return False
    
    return True

def main():
    """Main interactive function"""
    
    try:
        # Get user input
        product_name, product_num, rating_filter, next_pages = get_user_input()
        
        # Display summary and confirm
        if not display_summary(product_name, product_num, rating_filter, next_pages):
            sys.exit(0)
        
        print("\n🚀 Starting Amazon scraping workflow...")
        print("-" * 50)
        
        # Run the scraping workflow
        success = final_complete_workflow(
            search_term=product_name,
            max_products=product_num,
            rating_filter=rating_filter,
            next_pages=next_pages
        )
        
        # Display final result
        print("\n" + "=" * 50)
        if success:
            print("🎉 Interactive scraping completed successfully!")
            print("\n📁 Check the 'data' folder for generated files:")
            print(f"   • products_{product_name.replace(' ', '_')}_final.json")
            if rating_filter:
                print(f"   • reviews_[ASIN]_{rating_filter}.json (for each product)")
            else:
                print(f"   • reviews_[ASIN]_all.json (for each product)")
        else:
            print("❌ Interactive scraping failed!")
            print("   Please check the error messages above.")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user (Ctrl+C)")
        print("❌ Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
