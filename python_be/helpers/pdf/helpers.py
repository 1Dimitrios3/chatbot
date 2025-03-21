import os
import shutil
import threading
import chromadb
import openai
import hashlib
import datetime
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
STORAGE_PATH = os.getenv("CHROMA_STORAGE_PATH", "./chroma_storage")
_model_lock = threading.Lock()
_sentence_model = None

def get_sentence_model():
    global _sentence_model
    if _sentence_model is None:
        with _model_lock:
            if _sentence_model is None:
                _sentence_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return _sentence_model

# Initialize ChromaDB
# if there is a problem with chromaDB stale cache set reset to True
def initialize_chroma_client(storage_path, reset=False):
    """
    Initialize a new ChromaDB PersistentClient with the given storage path.
    If reset is True, remove existing storage before initializing.
    """
    if reset:
        if os.path.exists(storage_path):
            print(f"Removing existing storage at: {storage_path}")
            shutil.rmtree(storage_path)
        else:
            print(f"No existing storage found at: {storage_path}")
    else:
        if os.path.exists(storage_path):
            print(f"Using existing storage at: {storage_path}")
        else:
            print(f"No existing storage found at: {storage_path}")
    
    client = chromadb.PersistentClient(path=storage_path)
    print(f"Initialized ChromaDB client with storage path: {storage_path}")
    return client

# Set your storage path and initialize the client
chroma_client = initialize_chroma_client(STORAGE_PATH)

# Initialize collections
collection = chroma_client.get_or_create_collection(
    name="docs",  
    metadata={
        "hnsw:M": 64,       # Controls number of edges per node (16 - 64)
    }
)
metadata_collection = chroma_client.get_or_create_collection(name="metadata")


def get_pdf_hash(pdf_path: str) -> str:
    """Generate a SHA-256 hash for a PDF file."""
    hasher = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def mark_pdf_as_processed(pdf_path, num_chunks, pdf_hash):
    """Store PDF hash in metadata collection.
    """
    # Recalculate the pdf_hash to ensure consistency
    pdf_hash = get_pdf_hash(pdf_path)
    try:
        metadata_collection.add(
            ids=[pdf_hash],
            documents=["chat_docs"],  # Dummy value to satisfy requirements
            metadatas=[{
                "file": os.path.basename(pdf_path),
                "processed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "num_chunks": num_chunks,
                "pdf_hash": pdf_hash 
            }]
        )
        print(f"[DEBUG] Marked {pdf_path} as processed with {num_chunks} chunks.")
    except Exception as e:
        print(f"[ERROR] Error marking PDF as processed: {e}")


def get_pdf_metadata(pdf_path):
    """Retrieve metadata for a processed PDF as a dictionary."""
    pdf_hash = get_pdf_hash(pdf_path)
    results = metadata_collection.query(
        query_texts=[pdf_hash],
        n_results=1
    )
    if "metadatas" in results and results["metadatas"]:
        # Flatten the results in case it's a list of lists.
        meta_list = []
        for group in results["metadatas"]:
            if isinstance(group, list):
                meta_list.extend(group)
            else:
                meta_list.append(group)
        if meta_list:
            return meta_list[0]  # Return the first metadata dictionary.
    return None

def list_all_embeddings():
    """Fetch and print all stored embedding IDs in ChromaDB."""
    try:
        results = collection.get()  # Fetch all documents
    except Exception as e:
        print(f"❌ Error retrieving embeddings: {e}")
        return {"status": "error", "message": "Failed to list embeddings. Please try again later."}

    if "ids" in results and results["ids"]:
        count = len(results["ids"])
        print(f"✅ Found {count} embeddings in ChromaDB: Showing first 20 results.")
        for i, doc_id in enumerate(results["ids"][:20]):  # Show only first 20 results
            print(f"{i+1}. {doc_id}")
        return {"status": "success", "count": count}
    else:
        print("ℹ️ No embeddings found in ChromaDB.")
        return {"status": "empty", "message": "No embeddings found in ChromaDB."}


def clear_all_embeddings(reset=False):
    """Delete all stored embeddings from the collection."""
    try:
        results = collection.get()  # Fetch all documents
    except Exception as e:
        print(f"❌ Error retrieving embeddings: {e}")
        return {"status": "error", "message": "Failed to list embeddings. Please try again later."}
    all_ids = results.get("ids", [])
    if all_ids:
        collection.delete(ids=all_ids)
        print(f"Cleared {len(all_ids)} embeddings from the collection.")
    else:
        print("No embeddings found to clear.")

    # If reset=True, remove the entire storage folder
    if reset:
        storage_path = STORAGE_PATH
        if os.path.exists(storage_path):
            shutil.rmtree(storage_path)
            print(f"✅ Deleted all ChromaDB storage at: {storage_path}")
        else:
            print("ℹ️ No storage directory found. Nothing to delete.")

def clear_pdf_embeddings(pdf_path):
    """
    Check if embeddings for the given PDF file exist, and if so, clear them.

    This function:
      1. Computes the PDF's hash.
      2. Retrieves the metadata record for the PDF (which includes the number of chunks).
      3. If metadata exists, deletes all embeddings associated with that PDF from the collection.
      4. Deletes the metadata record from the metadata collection.
    """
    pdf_hash = get_pdf_hash(pdf_path)
    print(f"[DEBUG] Attempting to clear embeddings for PDF: {pdf_path} (hash: {pdf_hash})")
    
    # Retrieve metadata for this PDF.
    metadata = get_pdf_metadata(pdf_path)
    
    if metadata is None:
        print(f"[INFO] No metadata found for {pdf_path}. No embeddings to clear.")
        return

    num_chunks = metadata.get("num_chunks", 0)
    print(f"[DEBUG] Metadata found with {num_chunks} chunks for {pdf_path}.")
    
    # Build list of chunk IDs for deletion.
    chunk_ids = [f"{pdf_hash}_chunk_{i}" for i in range(num_chunks)]
    
    # Delete the embeddings (chunks) from the main collection.
    try:
        collection.delete(ids=chunk_ids)
        print(f"[DEBUG] Deleted {len(chunk_ids)} embeddings for {pdf_path}.")
    except Exception as e:
        print(f"[ERROR] Failed to delete embeddings for {pdf_path}: {e}")
    
    # Delete the associated metadata record.
    try:
        metadata_collection.delete(ids=[pdf_hash])
        print(f"[DEBUG] Deleted metadata record for {pdf_path}.")
    except Exception as e:
        print(f"[ERROR] Failed to delete metadata for {pdf_path}: {e}")

# def embed_text(text):
#     """Generate embeddings for a text chunk using openai api."""
#     response = openai.embeddings.create(
#         input=text,
#         model="text-embedding-ada-002" # text-embedding-3-small, text-embedding-3-large newest models
#     )
#     return response.data[0].embedding

# embed text with opensource alternative model (all-MiniLM-L6-v2) offers faster processing times
# use different chroma storage path as now the dimensionality is different
def embed_text(text):
    """Generate embeddings for a text chunk using all-MiniLM-L6-v2 sentence transformer (found in hugging face website)."""
    model = get_sentence_model()
    embedding = model.encode(text)
    return embedding.tolist()

def search_docs(query, top_k=10, min_score=0.7):
    """Retrieve relevant document chunks using embeddings."""
    query_embedding = embed_text(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    
    # Extract text from retrieved results
    retrieved_texts = []
    for group in results.get("metadatas", []):
        for doc in group:
            score = doc.get("score", 1)  # Default score if not provided
            if score >= min_score and "text" in doc:
                retrieved_texts.append(doc["text"])
    
    return retrieved_texts

def openai_stream_generator(response_iterator, session_id, chat_histories):
    """Stream OpenAI response while storing it in chat history."""
    full_response = ""

    for chunk in response_iterator:
        # The chunk has a structure like chunk.choices[0].delta.content
        # or chunk.choices[0].text, depending on the model
        delta = chunk.choices[0].delta
        if delta.content is not None:
            full_response += delta.content
            yield delta.content

    # ✅ Store final response in chat history
    if session_id in chat_histories:
        chat_histories[session_id].append({"role": "assistant", "content": full_response})

        # Keep only the last 12 entries (6 user queries + 6 AI responses)
        chat_histories[session_id] = chat_histories[session_id][-12:]