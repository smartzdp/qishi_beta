import logging
import time

from langchain_community.document_loaders import PyMuPDFLoader

from elastic_search import ESClient
from utils import split_documents_into_chunks, chunk_audio_segments
from embedding import embedding
from extract import extract_images_from_pdf, extract_tables_from_pdf, transcribe_audio


def ingest_pdf(es, es_index, file_path, include_image=False, include_table=False):
    """Ingest PDF file and index documents to Elasticsearch."""
    print(f"Ingesting file: {file_path}")
    loader = PyMuPDFLoader(file_path)  # 如果报错则使用PyMuPDFLoader处理pdf文件
    pages = loader.load()
    ################# 用Cluster生成文件摘要 ################
    # try:
    #     file_summary = generate_summary_for_file(subtitle, pages, file_id, None, user_id, base_id)
    # except Exception as e:
    #     pass

    ################# 提取图片和表格 ################
    # Extract images and tables based on parameters
    images = extract_images_from_pdf(file_path) if include_image else []
    tables = extract_tables_from_pdf(file_path) if include_table else []
    
    chunks = split_documents_into_chunks(pages, chunk_size=1024, chunk_overlap=100)
    batch = []
    for i, chunk in enumerate(chunks):  # 收集25个chunks为一批送到嵌入模型，增加速度
        batch.append(chunk)

        if len(batch) == 25 or i == len(chunks) - 1:
            embeddings = embedding([b.page_content for b in batch])
            for j, pc in enumerate(batch):
                # Add type and file_path to metadata
                metadata = {k: str(v) for k, v in pc.metadata.items() if v and str(v).strip()}
                metadata["type"] = "text"
                metadata["file_path"] = file_path
                
                body = {
                    "text": pc.page_content,
                    "vector": embeddings[j],
                    "metadata": metadata,
                }
                retry = 0
                while retry <= 5:
                    try:
                        # print(body)
                        es.index(index=es_index, body=body)  # 写入elastic
                        break
                    except Exception as e:
                        print(f"[Elastic Error] {str(e)} retry")
                    retry += 1
                    time.sleep(1)
            batch = []
    
    print("Text ingestion completed")

    # Process images
    if images:
        image_texts = [img["context_augmented_summary"] for img in images]
        image_embeddings = embedding(image_texts)
        for i, img in enumerate(images):
            # Add type and file_path to metadata
            metadata = {k: str(v) for k, v in img.items() if k != "context_augmented_summary" and v and str(v).strip()}
            metadata["type"] = "image"
            metadata["file_path"] = file_path
            
            body = {
                "text": img["context_augmented_summary"],
                "vector": image_embeddings[i],
                "metadata": metadata,
            }
            retry = 0
            while retry <= 5:
                try:
                    es.index(index=es_index, body=body)
                    break
                except Exception as e:
                    print(f"[Elastic Error] {str(e)} retry")
                    retry += 1
                    time.sleep(1)
        
        print("Image ingestion completed")

    # Process tables
    if tables:
        table_texts = [table["context_augmented_table"] for table in tables]
        table_embeddings = embedding(table_texts)
        for i, table in enumerate(tables):
            # Add type and file_path to metadata
            metadata = {k: str(v) for k, v in table.items() if k != "context_augmented_table" and v and str(v).strip()}
            metadata["type"] = "table"
            metadata["file_path"] = file_path
            
            body = {
                "text": table["context_augmented_table"],
                "vector": table_embeddings[i],
                "metadata": metadata,
            }
            retry = 0
            while retry <= 5:
                try:
                    es.index(index=es_index, body=body)
                    break
                except Exception as e:
                    print(f"[Elastic Error] {str(e)} retry")
                    retry += 1
                    time.sleep(1)
        
        print("Table ingestion completed")


def ingest_audio(es, es_index, file_path, json_path=None, chunk_size=256, chunk_overlap=128):
    """Ingest audio file and index transcribed chunks to Elasticsearch."""
    print(f"Ingesting audio file: {file_path}")
    
    # Transcribe audio file
    metadata, segments = transcribe_audio(file_path, json_path)
    print(f"Audio metadata: {metadata}")
    
    if not segments:
        print("No audio segments found")
        return
    
    # Chunk audio segments
    chunks = chunk_audio_segments(segments, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    print(f"Created {len(chunks)} audio chunks")
    
    # Process chunks in batches
    batch = []
    for i, chunk in enumerate(chunks):
        batch.append(chunk)
        
        if len(batch) == 25 or i == len(chunks) - 1:
            embeddings = embedding([b.page_content for b in batch])
            for j, pc in enumerate(batch):
                # Add type and file_path to metadata
                metadata_dict = {k: str(v) for k, v in pc.metadata.items() if v and str(v).strip()}
                metadata_dict["type"] = "audio"
                metadata_dict["file_path"] = file_path
                metadata_dict["language"] = metadata.get("language", "unknown")
                metadata_dict["duration"] = str(metadata.get("duration", 0))
                
                body = {
                    "text": pc.page_content,
                    "vector": embeddings[j],
                    "metadata": metadata_dict,
                }
                retry = 0
                while retry <= 5:
                    try:
                        es.index(index=es_index, body=body)
                        break
                    except Exception as e:
                        print(f"[Elastic Error] {str(e)} retry")
                        retry += 1
                        time.sleep(1)
            batch = []
    
    print("Audio ingestion completed")


