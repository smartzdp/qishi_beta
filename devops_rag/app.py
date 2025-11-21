import os
import sys
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# Ensure logs go to stdout for App Runner and flush immediately
import sys
sys.stdout.reconfigure(line_buffering=True)  # Enable line buffering for real-time logs

print("=" * 50, flush=True)
print("Starting BEE EDU RAG Application", flush=True)
print("=" * 50, flush=True)

# 1. Check API Key - warn if not set but don't fail immediately
# In AWS App Runner, this will be injected by AWS Secrets Manager
if "OPENAI_API_KEY" not in os.environ:
    print("⚠️  WARNING: OPENAI_API_KEY environment variable not set. Chat functionality will fail.", flush=True)
else:
    print("✅ OPENAI_API_KEY is set", flush=True)

print(f"Python version: {sys.version}", flush=True)
print(f"Working directory: {os.getcwd()}", flush=True)
print(f"FAISS index exists: {os.path.exists('faiss_index')}", flush=True)

# --- Lazy loading: Initialize RAG components on first use ---
rag_chain = None

def get_rag_chain():
    global rag_chain
    if rag_chain is None:
        print("Loading RAG model and vector store...")
        try:
            embeddings = OpenAIEmbeddings()
            vectorstore = FAISS.load_local(
                "faiss_index", 
                embeddings, 
                allow_dangerous_deserialization=True 
            )
            retriever = vectorstore.as_retriever()
        except Exception as e:
            print(f"⚠️  Error loading FAISS index: {e}")
            raise
        
        # RAG Prompt template
        template = """Use the following pieces of context to answer the question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context: {context}

Question: {question}

Helpful Answer: """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        # LLM model
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        
        # RAG Chain using LCEL
        def format_docs(docs):
            return "\n\n".join([d.page_content for d in docs])
        
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        print("✅ RAG Application is ready.")
    return rag_chain

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Log when the application starts - important for App Runner health checks"""
    print("=" * 50, flush=True)
    print("🚀 FastAPI application is starting...", flush=True)
    print(f"Listening on 0.0.0.0:8080", flush=True)
    print("=" * 50, flush=True)

class Query(BaseModel):
    question: str

@app.get("/")
def read_root():
    return {"message": "BEE EDU RAG Application is live!", "version": "v1"}

@app.get("/health")
def health_check():
    """Health check endpoint for App Runner"""
    return {"status": "healthy", "message": "Service is running"}

@app.post("/chat")
def chat(query: Query):
    try:
        # Lazy load RAG chain on first use
        chain = get_rag_chain()
        answer = chain.invoke(query.question)
        return {"answer": f"Helpful Answer: V4 {answer}"}
    except Exception as e:
        # Log the error for debugging
        print(f"❌ Error in chat endpoint: {e}", flush=True)
        # Return error message
        return {"error": str(e)}, 500
