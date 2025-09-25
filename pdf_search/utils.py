import tiktoken
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


def count_tokens_in_text(text: str) -> int:
    """Calculate number of tokens in a text string using tiktoken."""
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(text))
    return num_tokens


def create_document_splitter(chunk_size: int = 1024, chunk_overlap: int = 100):
    """Create a text splitter with specified parameters for document chunking."""
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap, 
        length_function=count_tokens_in_text
    )


def split_documents_into_chunks(documents, chunk_size: int = 1024, chunk_overlap: int = 100):
    """Split documents into chunks using the text splitter."""
    splitter = create_document_splitter(chunk_size, chunk_overlap)
    chunks = splitter.split_documents(documents)
    return chunks


def truncate_text(text: str, max_length: int = 1500) -> str:
    """Truncate text to specified length with ellipsis indicator."""
    if text is None:
        return ""
    text = text.strip()
    if len(text) <= max_length:
        return text
    return text[:max_length] + "\n... [truncated]"


def chunk_audio_segments(segments, chunk_size: int = 256, chunk_overlap: int = 128):
    """Group short transcript lines into larger chunks."""    
    seg_texts = [seg["text"].strip() + " " for seg in segments]
    seg_sizes = [count_tokens_in_text(text) for text in seg_texts]

    n = len(segments)
    start_idx = 0
    end_idx = 0
    curr_size = 0
    chunks = []

    while end_idx < n:
        while end_idx < n and curr_size < chunk_size:
            curr_size += seg_sizes[end_idx]
            end_idx += 1
        if end_idx == n:
            while start_idx > 0 and curr_size < chunk_size:
                start_idx -= 1
                curr_size += seg_sizes[start_idx]
        
        text = "".join(seg_texts[i] for i in range(start_idx, end_idx))
        chunks.append(
            Document(
                page_content=text,
                metadata={
                    "start_time": segments[start_idx]["start"],
                    "end_time": segments[end_idx - 1]["end"],
                    "duration": segments[end_idx - 1]["end"] - segments[start_idx]["start"],
                    "start_segment": start_idx,
                    "end_segment": end_idx - 1,
                    "segments": end_idx - start_idx,
                    "tokens": count_tokens_in_text(text),
                },
            )
        )

        start_idx = end_idx
        curr_size = 0
        while start_idx > 0 and curr_size < chunk_overlap:
            start_idx -= 1
            curr_size += seg_sizes[start_idx]

    return chunks
