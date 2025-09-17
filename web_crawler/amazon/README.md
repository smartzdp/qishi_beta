# Amazon Scraper - Modular System

A comprehensive, modular Amazon product and review scraper built with Patchright (Playwright).

## 🚀 Quick Start

### 1. Interactive Mode (Recommended)
```bash
cd amazon
./scrape.sh
```

### 2. Manual Execution
```bash
cd amazon
./run_clean.sh python3 interactive_scraper.py
```

## 📋 Interactive Configuration

The interactive script prompts for:
- **Product name** (default: "smart lock")
- **Number of products** (default: 3, range: 1-10)
- **Review rating filter** (default: none, options: 1-5 stars)
- **Additional review pages** (default: 1, range: 0-5)

Example session:
```
🚀 Interactive Amazon Scraper
==================================================
📝 Product name (default: smart lock): wireless headphones
📊 Number of products (default: 3): 5
⭐ Review rating filter (1-5, or press Enter for none): 5
📄 Additional review pages (default: 1): 2

✅ Proceed with scraping? (y/N): y
```

## 🏗️ Architecture

### Core Components
- **`interactive_scraper.py`** - User-friendly terminal interface
- **`final_complete_workflow.py`** - Complete automation workflow
- **`login_component.py`** - Amazon login/logout handling
- **`product_search_component.py`** - Product search and extraction
- **`review_search_component_simple.py`** - Advanced review extraction

### Utility Scripts
- **`scrape.sh`** - Convenience launcher
- **`run_clean.sh`** - Environment setup (handles zsh issues)

## ✨ Features

### 🔐 Smart Authentication
- **Dynamic login URL extraction** - No hardcoded URLs
- **Automatic logout detection** - Logs out existing sessions first
- **Secure credential handling** - Stored in `credentials.txt`

### 🔍 Advanced Product Search
- **Search bar interaction** - Uses actual Amazon search
- **Rich data extraction** - Title, ASIN, price, rating, reviews, URL
- **Configurable product count** - 1-10 products
- **Smart price parsing** - Handles decimals and formats correctly

### ⭐ Sophisticated Review Extraction
- **Star rating filters** - Filter by 1-5 stars or get all reviews
- **Multi-page pagination** - Scrape multiple pages of reviews
- **Detailed review data** - Name, rating, title, text, date, location, verified purchase
- **Robust extraction** - Handles various Amazon review page formats

### 🛡️ Reliability Features
- **Error handling** - Graceful fallbacks and detailed logging
- **Anti-bot measures** - Stealth browser configuration
- **Rate limiting** - Respects Amazon's servers
- **Session management** - Maintains browser state across operations

## 📊 Output Data

### Product Files
`products_[search_term]_final.json`:
```json
[
  {
    "rank": 1,
    "name": "Product Name",
    "asin": "B123456789",
    "price": 99.99,
    "rating": "4.5",
    "reviews": "1.2K",
    "url": "https://amazon.com/product-url"
  }
]
```

### Review Files
`reviews_[ASIN]_[rating].json`:
```json
[
  {
    "reviewerName": "John Doe",
    "rating": 5,
    "title": "Great product!",
    "location": "United States",
    "date": "January 15, 2024",
    "verifiedPurchase": true,
    "reviewText": "This product exceeded my expectations...",
    "page": 1
  }
]
```

## 🔧 Configuration

### Environment Setup
1. **Virtual Environment**: Must be activated before running
2. **Dependencies**: Install via `pip install -r requirements.txt`
3. **Credentials**: Configure your Amazon credentials in `credentials.txt`
   ```
   your_email@example.com
   your_password_here
   ```
   **⚠️ Important**: Replace with your actual Amazon email and password

### Search Parameters
- **Product Categories**: Any Amazon search term
- **Product Limits**: 1-10 products per search
- **Review Filters**: None, 1-star, 2-star, 3-star, 4-star, 5-star
- **Page Limits**: 0-5 additional pages (1-6 total pages)

## 📁 File Structure

```
amazon/
├── interactive_scraper.py          # 🎯 Main interface
├── final_complete_workflow.py      # 🔧 Workflow engine
├── login_component.py              # 🔐 Login handling
├── product_search_component.py     # 🔍 Product search
├── review_search_component_simple.py # ⭐ Review extraction
├── scrape.sh                       # 🚀 Launcher
├── run_clean.sh                    # 🛠️ Environment setup
├── credentials.txt                 # 🔑 Login credentials
├── requirements.txt                # 📦 Dependencies
├── README.md                       # 📖 Documentation
└── data/                           # 📊 Output files
    ├── products_*.json             # Product data
    └── reviews_*.json              # Review data
```

## 🚨 Troubleshooting

### Zsh Error (`dump_zsh_state`)
**Solution**: Use the wrapper scripts
```bash
./scrape.sh                                    # Recommended
./run_clean.sh python3 interactive_scraper.py # Manual
```

### Login Issues
- ✅ Verify credentials in `credentials.txt`
- ✅ Check for 2FA requirements on your Amazon account
- ✅ Try running in non-headless mode for debugging
- ✅ Ensure you're not already logged in elsewhere

### No Products Found
- ✅ Check internet connection
- ✅ Verify search term returns results on Amazon
- ✅ Try different, more specific search terms
- ✅ Check if Amazon is blocking automated requests

### Review Extraction Issues
- ✅ Ensure you're logged in successfully
- ✅ Try different star rating filters
- ✅ Reduce the number of pages requested
- ✅ Check if the product has reviews for the selected rating

## 🔒 Security & Ethics

- **Credential Security**: 
  - Never commit `credentials.txt` to version control (protected by `.gitignore`)
  - Replace example credentials with your real Amazon login
  - Keep your credentials file secure and private
- **Rate Limiting**: Built-in delays to respect Amazon's servers
- **Terms of Service**: Use responsibly and in accordance with Amazon's ToS
- **Personal Use**: Intended for research and personal use only

## 📋 Requirements

- **Python 3.7+**
- **patchright** - Browser automation
- **Valid Amazon credentials**
- **Stable internet connection**
- **Virtual environment activated**

## 🎯 Usage Examples

### Basic Product Research
```bash
# Search for 3 smart locks, no reviews
./scrape.sh
# Choose: smart lock, 3, none, 1
```

### Comprehensive Review Analysis
```bash
# Search for 5 wireless headphones, get 5-star reviews, 3 pages each
./scrape.sh
# Choose: wireless headphones, 5, 5, 2
```

### Quick Single Product Check
```bash
# Search for 1 laptop, get all reviews, 1 page
./scrape.sh  
# Choose: laptop, 1, none, 0
```

---

**Built with ❤️ using modular architecture for maximum flexibility and reliability.**