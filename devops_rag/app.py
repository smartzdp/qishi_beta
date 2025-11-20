import os
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# 1. Check API Key - warn if not set but don't fail immediately
# In AWS App Runner, this will be injected by AWS Secrets Manager
if "OPENAI_API_KEY" not in os.environ:
    print("⚠️  WARNING: OPENAI_API_KEY environment variable not set. Chat functionality will fail.")
else:
    print("✅ OPENAI_API_KEY is set")

# --- Lazy loading: Initialize RAG components on first use ---
rag_chain = None

def get_rag_chain():
    global rag_chain
    if rag_chain is None:
        print("Loading RAG model and vector store...")
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.load_local(
            "faiss_index", 
            embeddings, 
            allow_dangerous_deserialization=True 
        )
        retriever = vectorstore.as_retriever()
        
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

class Query(BaseModel):
    question: str

@app.get("/")
def read_root():
    return {"message": "RAG Application is live!", "version": "v1"}

@app.post("/chat")
def chat(query: Query):
    try:
        # Lazy load RAG chain on first use
        chain = get_rag_chain()
        answer = chain.invoke(query.question)
        return {"answer": answer}
    except Exception as e:
        # Return error message
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
