import os
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# 确保 API Key 存在
if "OPENAI_API_KEY" not in os.environ:
    raise EnvironmentError("请先设置 OPENAI_API_KEY 环境变量")

# 加载文档
loader = TextLoader("./data.txt")
documents = loader.load()

# 分割文档
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

# 创建向量并存储
embeddings = OpenAIEmbeddings()
db = FAISS.from_documents(docs, embeddings)

# 保存到本地
db.save_local("faiss_index")
print("✅ FAISS index has been saved to 'faiss_index'")