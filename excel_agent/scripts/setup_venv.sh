#!/bin/bash

# Setup virtual environment for Excel Agent

set -e

echo "🚀 Setting up Excel Agent virtual environment..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $python_version"

if [[ "$python_version" < "3.10" ]]; then
    echo "❌ Python 3.10+ is required"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Verify installation
echo "✅ Verifying installation..."
python -c "import fastapi; import pandas; import sentence_transformers; print('✅ All core dependencies installed')"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env and fill in your API keys"
echo "  2. Run: bash scripts/ingest_samples.sh"
echo "  3. Run: bash scripts/dev_server.sh"

