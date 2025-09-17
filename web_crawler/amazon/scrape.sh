#!/bin/bash
# Interactive Amazon Scraper Launcher
# Usage: ./scrape.sh

cd "$(dirname "$0")"
./run_clean.sh python3 interactive_scraper.py
