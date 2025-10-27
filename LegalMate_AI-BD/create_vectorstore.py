import os
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from langchain_chroma import Chroma

# --- Use Environment Variable for Consistency ---
load_dotenv()
PERSIST_DIRECTORY = os.getenv("CHROMA_DB_PATH", "chroma_db")

def create_vector_store():
    loader = DirectoryLoader(
        'legal_docs/', 
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True
    )
    documents = loader.load()
    
    if not documents:
        print("No PDF documents found.")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    print(f"Created {len(texts)} text chunks.")

    print("Initializing Cohere embedding model...")
    cohere_api_key = os.getenv("COHERE_API_KEY")
    if not cohere_api_key:
        raise ValueError("COHERE_API_KEY not found in .env file.")
    
    embeddings = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=cohere_api_key)
    
    print(f"Creating and persisting vector store in '{PERSIST_DIRECTORY}'...")

    # --- BATCHING LOGIC TO AVOID RATE LIMITS ---
    batch_size = 90  # Process 90 chunks per batch (under the 100 limit)
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}...")
        
        if i == 0:
            # For the first batch, create the Chroma DB
            db = Chroma.from_documents(
                batch, 
                embeddings, 
                persist_directory=PERSIST_DIRECTORY
            )
        else:
            # For subsequent batches, add to the existing DB
            db.add_documents(batch)
        
        # If it's not the last batch, wait for 61 seconds before the next one
        if i + batch_size < len(texts):
            print("Rate limit cooldown: Waiting for 61 seconds...")
            time.sleep(61)

    print("Vector store created successfully using Cohere model!")

if __name__ == "__main__":
    create_vector_store()