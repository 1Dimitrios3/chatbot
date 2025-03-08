import os
import streamlit as st
import json
from helpers.pdf.helpers import initialize_chroma_client

# Set storage path, configurable via environment variable
STORAGE_PATH = os.getenv("CHROMA_STORAGE_PATH", "./chroma_storage")

# Initialize ChromaDB using the custom helper function
# Set reset=True to clear any existing storage; otherwise, use existing state.
chroma_client = initialize_chroma_client(STORAGE_PATH, reset=False)
collection = chroma_client.get_or_create_collection(name="docs")

# Define number of items per page
PAGE_SIZE = 10


def fetch_all_ids():
    """Retrieve all stored IDs in ChromaDB."""
    results = collection.peek()
    return results.get("ids", []), results.get("metadatas", [])


def fetch_embedding_by_id(doc_id):
    """Retrieve embeddings for a given document ID using a ChromaDB query."""
    result = collection.query(ids=[doc_id], n_results=1)
    embeddings = result.get("embeddings", [[]])
    return embeddings[0] if embeddings and embeddings[0] else None


def view_embeddings():
    """Streamlit UI to explore stored embeddings, metadata, and document IDs."""
    st.title("🔍 ChromaDB Embeddings Viewer")
    
    ids, metadatas = fetch_all_ids()

    if not ids:
        st.warning("⚠️ No embeddings found in ChromaDB.")
        return

    # Paginate results
    num_pages = (len(ids) + PAGE_SIZE - 1) // PAGE_SIZE
    page = st.number_input("Page", min_value=1, max_value=num_pages, step=1) - 1

    # Display metadata and IDs
    st.write(f"📂 Showing {PAGE_SIZE} embeddings per page (Page {page + 1} of {num_pages})")

    for i in range(page * PAGE_SIZE, min((page + 1) * PAGE_SIZE, len(ids))):
        doc_id = ids[i]
        metadata = metadatas[i]

        with st.expander(f"🆔 Document ID: {doc_id}"):
            st.write("📜 **Metadata:**")
            st.json(metadata)

            # Optionally fetch embeddings
            if st.button(f"🔍 View Embedding for {doc_id}"):
                embedding = fetch_embedding_by_id(doc_id)
                if embedding:
                    st.write(f"🧬 **Embedding (first 100 values):** {embedding[:100]} ...")
                else:
                    st.error("⚠️ No embedding found for this document.")

    # Export Data Option
    if st.button("📥 Export All Metadata & IDs"):
        export_data = {"ids": ids, "metadatas": metadatas}
        json_data = json.dumps(export_data, indent=2)
        st.download_button("⬇️ Download JSON", json_data, file_name="chroma_metadata.json", mime="application/json")


view_embeddings()
