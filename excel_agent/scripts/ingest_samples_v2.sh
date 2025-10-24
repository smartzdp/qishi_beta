#!/bin/bash

# Ingest sample Excel files (Version 2: Using dismantle approach)

set -e

echo "📁 Ingesting sample Excel files (V2 - Dismantle approach)..."

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated. Activating..."
    source .venv/bin/activate
fi

# Check if samples directory exists
if [[ ! -d "data/samples" ]]; then
    echo "❌ data/samples directory not found"
    exit 1
fi

# Count sample files
sample_count=$(find data/samples -name "*.xlsx" -o -name "*.xls" | wc -l)
echo "Found $sample_count sample Excel files"

if [[ $sample_count -eq 0 ]]; then
    echo "❌ No Excel files found in data/samples/"
    exit 1
fi

# Set PYTHONPATH to include project root
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# Create a Python script to ingest files
cat > /tmp/ingest_samples_v2.py << 'EOF'
"""
Batch ingest sample files (V2 - Using dismantle approach)
"""
import sys
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from backend.services.preprocessing.dismantle import ExcelDismantler
from backend.services.preprocessing import DataFrameProfiler
from backend.services.rag import RAGIndexer
from backend.config import settings
import json

def main():
    samples_dir = Path("data/samples")
    
    if not samples_dir.exists():
        print("❌ data/samples directory not found")
        return
    
    # Get all Excel files
    excel_files = list(samples_dir.glob("*.xlsx")) + list(samples_dir.glob("*.xls"))
    
    print(f"📁 Processing {len(excel_files)} files...\n")
    
    dismantler = ExcelDismantler()
    profiler = DataFrameProfiler()
    
    all_summaries = []
    
    # Create output directories
    processed_dir = settings.data_dir / "processed_clean"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    for file_path in excel_files:
        print(f"📄 Processing: {file_path.name}")
        
        try:
            # Create output directory for this file
            file_output_dir = processed_dir / file_path.stem
            file_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Process Excel file (dismantle)
            result = dismantler.process_excel_file(file_path, file_output_dir)
            
            if result is None:
                print(f"  ❌ Failed to process file")
                continue
            
            print(f"  ✅ Original file: {result['original_file']}")
            print(f"  ✅ Sheet count: {result['sheet_count']}")
            
            # Process each sheet
            for sheet_name, sheet_info in result['sheets'].items():
                df = sheet_info['df']
                clean_file = sheet_info['file_path']
                
                print(f"  📊 Sheet: {sheet_name}")
                print(f"    ✅ Shape: {df.shape}")
                print(f"    ✅ Columns: {', '.join(list(df.columns)[:5])}...")
                print(f"    ✅ Saved: {Path(clean_file).name}")
                
                # Profile the cleaned data
                profile = profiler.profile(df, sheet_name)
                
                # Generate summary
                summary = profiler.generate_summary(
                    df, profile, sheet_name, file_path.name
                )
                
                # Add original file info
                summary['original_file'] = file_path.name
                summary['original_sheet_count'] = result['sheet_count']
                summary['all_sheets'] = list(result['sheets'].keys())
                summary['clean_excel_path'] = clean_file
                summary['had_merged_cells'] = sheet_info['had_merged_cells']
                
                all_summaries.append(summary)
                
                # Save metadata
                meta_file = file_output_dir / f"{sheet_name}_meta.json"
                from backend.services.rag.indexer import json_serializable
                meta_data = json_serializable({
                    'original_file': file_path.name,
                    'sheet_name': sheet_name,
                    'clean_excel_path': clean_file,
                    'shape': df.shape,
                    'columns': list(df.columns),
                    'profile': profile,
                    'summary': summary,
                    'original_sheet_count': result['sheet_count'],
                    'all_sheets': list(result['sheets'].keys())
                })
                
                with open(meta_file, 'w', encoding='utf-8') as f:
                    json.dump(meta_data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(f"  ❌ Error processing {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Build RAG index
    if all_summaries:
        print(f"\n🔍 Building RAG index from {len(all_summaries)} summaries...")
        indexer = RAGIndexer(
            knowledge_base_dir=settings.knowledge_base_dir,
            embedding_model=settings.embedding_model
        )
        indexer.build_index(all_summaries)
        print("✅ RAG index built successfully")
    
    print("\n✅ All samples processed!")
    print(f"📁 Processed files saved to: data/processed_clean/")
    print(f"🔍 RAG index saved to: data/knowledge_base/")

if __name__ == '__main__':
    main()
EOF

# Run the ingestion script
echo ""
python /tmp/ingest_samples_v2.py

# Clean up
rm /tmp/ingest_samples_v2.py

echo ""
echo "✅ Sample ingestion complete (V2)!"
echo ""
echo "You can now start the development server with:"
echo "  bash scripts/dev_server.sh"

