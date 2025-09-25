#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interactive Query Script for Elasticsearch Database
This script provides a conversational interface for querying PDF documents stored in Elasticsearch.
"""

import os
import sys
import json
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from elastic_search import ESClient
from rag.query import enhance_query
from rag.retrieve import enhance_retrieve
from rag.web_search import ask_llm, bocha_web_search
from openai import OpenAI
from config import OPENAI_API_KEY


class ChatSession:
    """Manages chat history and conversation state."""
    
    def __init__(self):
        self.chat_history = []
        self.session_data = []
    
    def add_interaction(self, query: str, enhanced_queries: List[str], 
                       results: Dict[str, List[Dict]], response: str):
        """Add a complete interaction to chat history."""
        interaction = {
            "query": query,
            "enhanced_queries": enhanced_queries,
            "results": results,
            "response": response
        }
        self.chat_history.append(interaction)
        self.session_data.append({"role": "user", "content": query})
        self.session_data.append({"role": "assistant", "content": response})
    
    def get_chat_history_for_enhancement(self) -> str:
        """Get formatted chat history for query enhancement."""
        if not self.chat_history:
            return ""
        
        history_str = ""
        for i, interaction in enumerate(self.chat_history[-5:], 1):  # Last 5 interactions
            history_str += f'"user": {interaction["query"]}\n'
            history_str += f'"assistant": {interaction["response"][:200]}...\n'
        
        return history_str.strip()


class ElasticsearchQueryInterface:
    """Main interface for querying Elasticsearch database."""
    
    def __init__(self):
        self.es_client = None
        self.current_index = None
        self.chat_session = ChatSession()
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
    def connect_to_elasticsearch(self):
        """Initialize connection to Elasticsearch."""
        print("🔗 Connecting to Elasticsearch...")
        try:
            self.es_client = ESClient()
            print("✓ Connected to Elasticsearch successfully")
        except Exception as e:
            print(f"❌ Failed to connect to Elasticsearch: {e}")
            return False
        return True
    
    def select_index(self) -> bool:
        """Allow user to enter an Elasticsearch index name."""
        print("\n📊 Enter Elasticsearch Index Name:")
        print("-" * 40)
        
        while True:
            try:
                index_name = input("Enter index name: ").strip()
                if not index_name:
                    print("Please enter a valid index name.")
                    continue
                
                # Validate that the index exists
                if self.es_client.index_exists(index_name):
                    self.current_index = index_name
                    print(f"✓ Index '{index_name}' found and selected")
                    return True
                else:
                    print(f"❌ Index '{index_name}' does not exist.")
                    print("Please create an index first using start_es_db.py or enter a valid index name.")
                    continue
                    
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return False
    
    def enhance_query_with_history(self, query: str) -> List[str]:
        """Enhance user query using chat history."""
        print("🔍 Enhancing query...")
        try:
            chat_history = self.chat_session.get_chat_history_for_enhancement()
            enhanced_queries = enhance_query(query, chat_history if chat_history else None)
            print(f"✓ Generated {len(enhanced_queries)} enhanced queries")
            return enhanced_queries
        except Exception as e:
            print(f"⚠️  Query enhancement failed: {e}")
            return [query]  # Fallback to original query
    
    def retrieve_documents(self, queries: List[str]) -> Dict[str, List[Dict]]:
        """Retrieve documents for each query."""
        print("📚 Retrieving documents...")
        results = {}
        
        for i, query in enumerate(queries, 1):
            print(f"  [{i}/{len(queries)}] Searching: {query[:50]}{'...' if len(query) > 50 else ''}")
            try:
                # Use chat history for coreference resolution in subsequent queries
                chat_history = self.chat_session.get_chat_history_for_enhancement() if i > 1 else None
                docs = enhance_retrieve(self.es_client.es, query, self.current_index, top_k=5)
                results[query] = docs
                print(f"    ✓ Found {len(docs)} documents")
            except Exception as e:
                print(f"    ❌ Failed to retrieve for query '{query}': {e}")
                results[query] = []
        
        return results
    
    def generate_response(self, original_query: str, enhanced_queries: List[str], 
                         results: Dict[str, List[Dict]]) -> str:
        """Generate comprehensive response using OpenAI GPT-5."""
        print("🤖 Generating response...")
        
        # Prepare context from all retrieved documents
        context_parts = []
        total_docs = 0
        
        for query, docs in results.items():
            if not docs:
                continue
            
            context_parts.append(f"Results for query: '{query}'")
            for i, doc in enumerate(docs, 1):
                doc_type = doc.get('metadata', {}).get('type', 'unknown')
                file_path = doc.get('metadata', {}).get('file_path', 'unknown')
                page_num = doc.get('metadata', {}).get('page', 'unknown')
                
                context_parts.append(f"\n{i}. [Document: {os.path.basename(file_path)}, "
                                   f"Page: {page_num}, Type: {doc_type}]")
                context_parts.append(f"Content: {doc['text'][:500]}{'...' if len(doc['text']) > 500 else ''}")
                total_docs += 1
        
        context = "\n".join(context_parts)
        
        # Check if no relevant documents were found
        if total_docs == 0:
            print("🔍 No relevant documents found in Elasticsearch database.")
            print("🌐 Searching web for additional information...")
            
            try:
                # Use web search as fallback
                web_search_results = bocha_web_search(original_query)
                web_response = ask_llm(original_query, web_search_results)
                
                return f"""I couldn't find relevant information in the Elasticsearch database to answer your question: "{original_query}"

However, I found some information through web search:

{web_response}

**Source**: Web Search
**Note**: This information was retrieved from web search and may not be from the documents in your database."""
                
            except Exception as e:
                print(f"⚠️  Web search failed: {e}")
                return f"""I couldn't find relevant information in the Elasticsearch database to answer your question: "{original_query}"

Unfortunately, I was also unable to search the web for additional information due to a technical error.

Please try rephrasing your question or ensure that the relevant documents have been properly indexed in the database."""
        
        # Create comprehensive prompt
        prompt = f"""You are an AI assistant helping users query a PDF document database stored in Elasticsearch. 

IMPORTANT INSTRUCTIONS:
- You MUST base your answer ONLY on the retrieved documents provided below
- Do NOT create or invent any information not present in the documents
- If the retrieved documents don't contain enough information to answer the question, start your response with "检索失败" and clearly state this
- Always provide specific references to the source documents, including document names, page numbers, and content types (text/image/table)
- Be precise and factual in your responses

USER QUESTION: {original_query}

RETRIEVED DOCUMENTS FROM ELASTICSEARCH:
{context}

Please provide a comprehensive answer to the user's question based on the retrieved documents above. If the documents don't contain sufficient information, start your response with "检索失败" and explain why. Otherwise, include specific references to:
1. Which documents contain relevant information
2. Page numbers where information was found  
3. Whether the information came from text, images, or tables
4. Direct quotes or paraphrases from the source material

Answer:"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on retrieved documents from an Elasticsearch database. Always provide accurate, source-based answers with proper references."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=20000,
                timeout=300
            )
            
            gpt_response = response.choices[0].message.content
            
            # Check if GPT response starts with "检索失败" (search failed)
            if gpt_response.strip().startswith("检索失败"):
                print("🔍 GPT detected insufficient information in retrieved documents.")
                print("🌐 Triggering web search as fallback...")
                
                try:
                    # Use web search as fallback
                    web_search_results = bocha_web_search(original_query)
                    
                    # Create specific prompt for web search when ES retrieval fails
                    web_prompt = f"""You are an AI assistant providing information from web search results because the user's document database didn't contain relevant information.

IMPORTANT INSTRUCTIONS:
- Answer the user's question based on the web search results provided below
- Do NOT include any "证据" (evidence) or "引用" (citation) sections
- Do NOT provide detailed source references or citations
- Focus on directly answering the question with the information found
- Keep the response concise and informative
- Do NOT mention that this is from web search in your response

USER QUESTION: {original_query}

WEB SEARCH RESULTS:
{web_search_results}

Please provide a direct answer to the user's question without including evidence or citation sections:"""
                    
                    web_response = self.openai_client.chat.completions.create(
                        model="gpt-5",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that answers questions based on web search results. Do not include evidence or citation sections."},
                            {"role": "user", "content": web_prompt}
                        ],
                        max_completion_tokens=1500,
                        timeout=60
                    ).choices[0].message.content
                    
                    return f"""**补充信息（来自网络搜索）**：

{web_response}

**来源**: 网络搜索
**注意**: 此信息来自网络搜索，可能不包含在您的数据库中。"""
                    
                except Exception as web_e:
                    print(f"⚠️  Web search failed: {web_e}")
                    return f"""**检索失败**: 在您的文档数据库中未找到相关信息。

**补充说明**: 尝试通过网络搜索获取补充信息时遇到技术错误。

请尝试重新表述您的问题，或确保相关文档已正确索引到数据库中。"""
            
            return gpt_response
            
        except Exception as e:
            print(f"❌ Failed to generate response: {e}")
            return f"I apologize, but I encountered an error while generating the response: {e}"
    
    def process_query(self, query: str):
        """Process a single user query through the complete pipeline."""
        print(f"\n🔍 Processing query: {query}")
        print("=" * 60)
        
        # Step 1: Enhance query
        enhanced_queries = self.enhance_query_with_history(query)
        
        # Step 2: Retrieve documents
        results = self.retrieve_documents(enhanced_queries)
        
        # Step 3: Generate response
        response = self.generate_response(query, enhanced_queries, results)
        
        # Step 4: Display response
        print("\n" + "=" * 60)
        print("💬 RESPONSE:")
        print("=" * 60)
        print(response)
        print("=" * 60)
        
        # Step 5: Update chat history
        self.chat_session.add_interaction(query, enhanced_queries, results, response)
        
        return response
    
    def interactive_session(self):
        """Run interactive query session."""
        print("🚀 Starting interactive query session...")
        print("Type 'quit', 'exit', or press Ctrl+C to end the session")
        print("Type 'help' for available commands")
        
        while True:
            try:
                print(f"\n📝 Query Index: {self.current_index}")
                user_input = input("\n💬 Enter your question: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                elif user_input.lower() == 'history':
                    self.show_chat_history()
                    continue
                elif user_input.lower() == 'clear':
                    self.chat_session = ChatSession()
                    print("✓ Chat history cleared")
                    continue
                
                # Process the query
                self.process_query(user_input)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ An error occurred: {e}")
    
    def show_help(self):
        """Display help information."""
        print("\n📖 Available Commands:")
        print("  help     - Show this help message")
        print("  history  - Show chat history")
        print("  clear    - Clear chat history")
        print("  quit/exit - End the session")
        print("\n💡 Tips:")
        print("  - Ask specific questions about your documents")
        print("  - The system will automatically enhance your queries")
        print("  - References to sources will be provided in responses")
    
    def show_chat_history(self):
        """Display chat history."""
        if not self.chat_session.chat_history:
            print("📝 No chat history yet.")
            return
        
        print("\n📝 Chat History:")
        print("-" * 40)
        for i, interaction in enumerate(self.chat_session.chat_history, 1):
            print(f"{i}. Q: {interaction['query']}")
            print(f"   A: {interaction['response'][:100]}{'...' if len(interaction['response']) > 100 else ''}")
            print()


def load_environment():
    """Load environment variables from .env file."""
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
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


def main():
    """Main function to run the query interface."""
    print("🔍 Elasticsearch PDF Query Interface")
    print("=" * 50)
    
    # Load environment variables
    load_environment()
    
    # Initialize interface
    interface = ElasticsearchQueryInterface()
    
    # Connect to Elasticsearch
    if not interface.connect_to_elasticsearch():
        return
    
    # Select index
    if not interface.select_index():
        return
    
    # Start interactive session
    interface.interactive_session()


if __name__ == "__main__":
    main()
