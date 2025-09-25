#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interactive PDF Ingestion Script for Elasticsearch
This script provides an interactive interface for ingesting PDF files into Elasticsearch.
"""

import os
import sys
import subprocess
import glob
from pathlib import Path

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from elastic_search import ESClient
from rag.ingest import ingest_pdf


def check_virtual_environment():
    """Check if virtual environment exists and is activated."""
    venv_path = Path("venv")
    if not venv_path.exists():
        print("❌ Virtual environment not found!")
        print("Please create a virtual environment first:")
        print("  python -m venv venv")
        print("  source venv/bin/activate")
        print("  pip install -r requirements.txt")
        return False
    
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Virtual environment may not be activated")
        print("Please run: source venv/bin/activate")
    
    return True


def load_environment():
    """Load environment variables from .env file."""
    env_file = Path(".env")
    if env_file.exists():
        print("Loading environment variables from .env...")
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            print("✓ Environment variables loaded")
        except Exception as e:
            print(f"⚠️  Warning: Failed to load .env file: {e}")
    else:
        print("⚠️  Warning: .env file not found, using system environment variables")
    print()


def get_user_input(prompt, validation_func=None, error_msg="Invalid input. Please try again."):
    """Get user input with optional validation."""
    while True:
        try:
            user_input = input(prompt).strip()
            if validation_func:
                if validation_func(user_input):
                    return user_input
                else:
                    print(error_msg)
            else:
                return user_input
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            sys.exit(0)
        except EOFError:
            print("\n\nOperation cancelled.")
            sys.exit(0)


def get_index_name():
    """Get Elasticsearch index name from user."""
    def validate_index_name(name):
        if not name:
            return False
        # Basic validation for Elasticsearch index names
        return all(c.isalnum() or c in '-_' for c in name)
    
    return get_user_input(
        "Enter Elasticsearch index name: ",
        validate_index_name,
        "Index name must contain only alphanumeric characters, hyphens, and underscores."
    )


def get_pdf_directory():
    """Get PDF directory path from user."""
    def validate_directory(path):
        if not path:
            return False
        path_obj = Path(path)
        if not path_obj.exists():
            print(f"Directory '{path}' does not exist.")
            return False
        if not path_obj.is_dir():
            print(f"'{path}' is not a directory.")
            return False
        return True
    
    return get_user_input(
        "Enter directory path containing PDF files: ",
        validate_directory,
        "Please enter a valid directory path."
    )


def get_boolean_input(prompt):
    """Get yes/no input from user."""
    while True:
        response = input(f"{prompt} (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please answer yes (y) or no (n).")


def find_pdf_files(directory):
    """Find all PDF files in the given directory."""
    pdf_patterns = ['*.pdf', '*.PDF']
    pdf_files = []
    
    for pattern in pdf_patterns:
        pdf_files.extend(glob.glob(os.path.join(directory, pattern)))
    
    return sorted(pdf_files)


def confirm_settings(index_name, pdf_directory, pdf_files, include_image, include_table):
    """Display settings and get user confirmation."""
    print("\n" + "="*60)
    print("📋 INGESTION SETTINGS SUMMARY")
    print("="*60)
    print(f"Index Name: {index_name}")
    print(f"PDF Directory: {pdf_directory}")
    print(f"Found PDF Files: {len(pdf_files)}")
    
    if pdf_files:
        print("\nPDF Files to be processed:")
        for i, file_path in enumerate(pdf_files[:5], 1):  # Show first 5 files
            print(f"  {i}. {os.path.basename(file_path)}")
        if len(pdf_files) > 5:
            print(f"  ... and {len(pdf_files) - 5} more files")
    
    print(f"\nImage Extraction: {'✓ Enabled' if include_image else '✗ Disabled'}")
    print(f"Table Extraction: {'✓ Enabled' if include_table else '✗ Disabled'}")
    print("="*60)
    
    return get_boolean_input("\nProceed with ingestion?")


def main():
    """Main interactive function."""
    print("🚀 PDF Ingestion Script for Elasticsearch")
    print("="*50)
    
    # Check virtual environment
    if not check_virtual_environment():
        return
    
    # Load environment variables
    load_environment()
    
    # Get user inputs
    print("📝 Configuration")
    print("-" * 20)
    index_name = get_index_name()
    
    pdf_directory = get_pdf_directory()
    
    # Find PDF files
    pdf_files = find_pdf_files(pdf_directory)
    if not pdf_files:
        print(f"❌ No PDF files found in '{pdf_directory}'")
        return
    
    print(f"✓ Found {len(pdf_files)} PDF files")
    
    # Get extraction options
    print("\n🔧 Extraction Options")
    print("-" * 20)
    include_image = get_boolean_input("Include image extraction?")
    include_table = get_boolean_input("Include table extraction?")
    
    # Confirm settings
    if not confirm_settings(index_name, pdf_directory, pdf_files, include_image, include_table):
        print("Operation cancelled.")
        return
    
    # Initialize Elasticsearch client
    print("\n🔗 Connecting to Elasticsearch...")
    try:
        es_client = ESClient()
        print("✓ Connected to Elasticsearch")
    except Exception as e:
        print(f"❌ Failed to connect to Elasticsearch: {e}")
        return
    
    # Create index
    print(f"\n📊 Creating index '{index_name}'...")
    try:
        es_client.create_index(
            index_name, 
            vector_dims=1024, 
            metadata_fields={"metadata": "object"}
        )
        print("✓ Index created successfully")
    except Exception as e:
        print(f"❌ Failed to create index: {e}")
        return
    
    # Process PDF files
    print(f"\n📄 Processing {len(pdf_files)} PDF files...")
    print("="*60)
    
    successful_files = 0
    failed_files = []
    
    for i, file_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {os.path.basename(file_path)}")
        
        try:
            ingest_pdf(
                es=es_client.es,
                es_index=index_name,
                file_path=file_path,
                include_image=include_image,
                include_table=include_table
            )
            print(f"✓ Successfully processed: {os.path.basename(file_path)}")
            successful_files += 1
        except Exception as e:
            print(f"❌ Failed to process {os.path.basename(file_path)}: {e}")
            failed_files.append((file_path, str(e)))
    
    # Final summary
    print("\n" + "="*60)
    print("📊 INGESTION COMPLETE")
    print("="*60)
    print(f"✓ Successfully processed: {successful_files} files")
    
    if failed_files:
        print(f"❌ Failed to process: {len(failed_files)} files")
        print("\nFailed files:")
        for file_path, error in failed_files:
            print(f"  • {os.path.basename(file_path)}: {error}")
    
    print(f"\n🎉 Ingestion completed! Index '{index_name}' is ready for queries.")
    print("You can now use the retrieve and query functions to search your documents.")


if __name__ == "__main__":
    main()
