import tiktoken
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
