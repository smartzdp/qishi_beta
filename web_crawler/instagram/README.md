# Instagram Password Encryption & Login

A complete, production-ready implementation of Instagram's password encryption and login system. This project replicates Instagram's frontend JavaScript encryption exactly, enabling secure programmatic login.

## ✨ Features

- **🔒 Exact Instagram encryption** - Replicates frontend JavaScript precisely
- **🔑 Real encryption keys** - Extracts current keys from Instagram's API  
- **🚀 Complete login flow** - CSRF token handling + encrypted login
- **🐍 Python & JavaScript** - Use either language
- **🛡️ Secure password input** - Hidden password entry
- **⚡ Multiple interfaces** - CLI, interactive, and API usage

## 📁 Project Structure

```
instagram/
├── main.py                      # Main entry point
├── README.md                    # This file
├── package.json                 # Node.js dependencies
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
│
├── src/                         # Core implementation
│   ├── encrypt_silent.js        # Silent encryption (for Python wrapper)
│   ├── instagram_encrypt_clean.js # Verbose encryption (standalone)
│   └── instagram_encrypt_wrapper.py # Python wrapper
│
├── examples/                    # Usage examples
│   ├── encrypt_password.py      # Interactive encryption
│   ├── encrypt_quick.py         # Command-line encryption
│   └── instagram_login.py       # Complete login example
│
├── utils/                       # Utilities
│   └── decode_result.js         # Decode encrypted passwords
│
└── source_code/                 # Instagram's original JavaScript
    ├── ITsc2blnRm8ls2D9hlK-sQcZmS_41fIbLwBh0y-ssWYLJrFENaOI1Yz0-edQDL1j
    └── Vm4NQ3UFW2u-PkunlxtCNj8v73rre7sw98QrnitdaapLS9lHi4cxzCqEBEJhWPrP
```

## 🚀 Quick Start

### **1. Install Dependencies**

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies (activate venv first)
cd ..
source venv/bin/activate
cd instagram
pip install -r requirements.txt
```

### **2. Quick Start**

```bash
# Main entry point (recommended)
python3 main.py

# Direct usage examples:
python3 examples/encrypt_password.py     # Interactive encryption
python3 examples/instagram_login.py      # Complete login
python3 examples/encrypt_quick.py password timestamp  # CLI encryption
```

## 📚 API Usage

### **Python API:**
```python
import sys
sys.path.append('src')
from instagram_encrypt_wrapper import InstagramEncryptionWrapper

# Initialize wrapper
wrapper = InstagramEncryptionWrapper()

# Encrypt password (uses current timestamp)
encrypted = wrapper.encrypt_password("your_password")
print(encrypted)
# Output: #PWD_INSTAGRAM_BROWSER:10:1758163617:base64_data
```

### **JavaScript API:**
```javascript
const { encryptPassword } = require('./src/instagram_encrypt_clean.js');

const encrypted = await encryptPassword(81, "52e5426b...", "password", "timestamp");
console.log(encrypted);
```

## 🔧 How It Works

### **Encryption Process:**
1. **Extract keys** from Instagram's HTTP headers
2. **Generate AES-256 key** using Web Crypto API
3. **Encrypt password** with AES-GCM (zero IV, timestamp as AAD)
4. **Encrypt AES key** with NaCl sealed box + Blake2b nonce
5. **Build envelope** with exact Instagram structure
6. **Format result** as `#PWD_INSTAGRAM_BROWSER:version:timestamp:base64_data`

### **Login Process:**
1. **Get CSRF token** from Instagram login page
2. **Encrypt password** using the encryption system
3. **Send POST request** to `/api/v1/web/accounts/login/ajax/`
4. **Handle response** and manage session

## ⚠️ Important Notes

- **Educational purposes only** - Respect Instagram's terms of service
- **Use your own credentials** - Never use others' accounts
- **Rate limiting** - Instagram has anti-bot measures
- **Two-factor auth** - May require additional handling

## 🔍 Technical Details

### **Encryption Algorithm:**
- **AES-GCM-256** for password encryption
- **NaCl sealed box** for AES key protection
- **Blake2b hashing** for sealed box nonce
- **Zero IV** (matches Instagram's implementation)

### **Key Management:**
- **Always fresh keys** - Extracts current keys from Instagram's API for every operation
- **No fallbacks** - Fails gracefully if keys cannot be obtained
- **Key rotation proof** - Automatically adapts when Instagram changes encryption keys
- **Real-time security** - Uses Instagram's latest encryption parameters

## 🛠️ Troubleshooting

### **Common Issues:**
- **"Module not found"** - Install dependencies with `npm install` and `pip install -r requirements.txt`
- **"Node.js not found"** - Install Node.js 16+ 
- **"Keys not found"** - Instagram may have rotated keys, extract fresh ones
- **"Login failed"** - Check credentials, 2FA, rate limiting

### **Debug Mode:**
Use `decode_result.js` to analyze encrypted password structure:
```bash
node decode_result.js
```
