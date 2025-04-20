import fitz  # PyMuPDF
import os
from helpers.pdf.helpers import *
from schemas.variables import *
import nltk
nltk.download('punkt_tab')
from nltk.tokenize import sent_tokenize

os.environ["TOKENIZERS_PARALLELISM"] = "false"

def add_document(id, text):
    """Store document embeddings in ChromaDB."""
    embedding = embed_text(text)
    collection.add(
        ids=[id],
        embeddings=[embedding],
        metadatas=[{"text": text}]
    )

def chunk_text(text, chunk_size=200, overlap=10):
    """Split text into overlapping chunks without breaking sentences,
       and handle sentences that exceed the chunk size by splitting them further.
       TIP: Chunk size is measured in words. Overlap is measured in sentences.
       """
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_size = 0

    def add_current_chunk():
        nonlocal current_chunk, current_size
        if current_chunk:
            print(f"[CHUNK DEBUG] Appending chunk with {current_size} words and {len(current_chunk)} sentences.", flush=True)
            # Append the current chunk
            chunks.append(" ".join(current_chunk))
            # Retain an overlap of the last few sentences
            current_chunk = current_chunk[-overlap:] if overlap < len(current_chunk) else current_chunk
            current_size = sum(len(s.split()) for s in current_chunk)

    for sentence in sentences:
        sentence_words = sentence.split()
        sentence_length = len(sentence_words)

        # If the sentence itself is longer than the chunk size, split it further.
        if sentence_length > chunk_size:
            # Flush any existing chunk first.
            add_current_chunk()
            print(f"[CHUNK DEBUG] Splitting long sentence with {sentence_length} words.", flush=True)
            # Split the long sentence into smaller parts.
            for i in range(0, sentence_length, chunk_size):
                sub_chunk = " ".join(sentence_words[i:i + chunk_size])
                # DEBUG: Print details of each sub-chunk created.
                print(f"[CHUNK DEBUG] Appending sub-chunk with {len(sub_chunk.split())} words.", flush=True)
                chunks.append(sub_chunk)
            continue  # Skip the rest of the loop for this sentence

        # If adding this sentence would exceed the chunk size, flush the current chunk.
        if current_size + sentence_length > chunk_size and current_chunk:
            add_current_chunk()

        # Add the sentence to the current chunk.
        current_chunk.append(sentence)
        current_size += sentence_length

    # Append any remaining sentences as the final chunk.
    if current_chunk:
        print(f"[CHUNK DEBUG] Appending final chunk with {current_size} words and {len(current_chunk)} sentences.", flush=True)
        chunks.append(" ".join(current_chunk))

    print(f"[CHUNK DEBUG] Total chunks created: {len(chunks)}", flush=True)
    return chunks


def process_pdf(pdf_path, chunk_size):
    filename = os.path.basename(pdf_path)
    print(f"Starting processing for: {filename}")
    """Extract text from a PDF, chunk it, and store embeddings only if necessary."""
    pdf_hash = get_pdf_hash(pdf_path)
    print(f"[DEBUG] Computed PDF hash: {pdf_hash}")
    metadata = get_pdf_metadata(pdf_path)

    if metadata and metadata.get("pdf_hash") == pdf_hash:
        message = f"✅ Skipping {filename}: Already processed."
        print(message)
        return {"status": "skipped", "message": message}  # Return message to API

    print(f"🔄 Processing {filename}...")

  # Open PDF using a context manager
    try:
        with fitz.open(pdf_path) as doc:
            num_pages = doc.page_count
            print(f"[DEBUG] Opened PDF with {num_pages} pages.")
            full_text = ""
            pages_text = []
            for i, page in enumerate(doc):
                page_text = page.get_text("text")
                pages_text.append(page_text)
                print(f"[DEBUG] Extracted text from page {i + 1}/{num_pages}.")
            full_text = "\n".join(pages_text)
    except Exception as e:
        error_message = f"[ERROR] Failed to open or read PDF {filename}: {e}"
        print(error_message)
        return {"status": "error", "message": error_message}

    print("[DEBUG] Finished text extraction from PDF.")

    print("[DEBUG] Starting chunking process...")
    chunks = chunk_text(full_text, chunk_size, int(chunk_size / 50))
    num_chunks = len(chunks)
    print(f"[DEBUG] Chunking complete: {num_chunks} chunks created.", flush=True)

    for i, chunk in enumerate(chunks):
        chunk_id = f"{pdf_hash}_chunk_{i}"
        print(f"[DEBUG] Processing chunk {i + 1}/{num_chunks}: {chunk_id}")

        # Check if the chunk is already stored before inserting
        try:
            existing_chunks = collection.get(ids=[chunk_id])
        except Exception as e:
            print(f"[ERROR] Error retrieving chunk {chunk_id} from collection: {e}")
            continue

        if "ids" in existing_chunks and existing_chunks["ids"]:
            print(f"⏭️ Skipping existing chunk {chunk_id}")
            continue

        print(f"[DEBUG] Embedding and adding chunk {i + 1}/{num_chunks}: {chunk_id} ...")
        try:
            add_document(chunk_id, chunk)
            print(f"[DEBUG] Chunk {chunk_id} successfully embedded and added.", flush=True)
        except Exception as e:
            print(f"[ERROR] Error embedding chunk {chunk_id}: {e}", flush=True)


    try:
        mark_pdf_as_processed(pdf_path, num_chunks, pdf_hash)
        print("[DEBUG] Marked PDF as processed.", flush=True)
        return {"status": "processed", "message": f"PDF {filename} successfully processed!"}
    except Exception as e:
        error_message = f"[ERROR] Error marking PDF as processed: {e}"
        print(error_message)
        return {"status": "error", "message": error_message}



def process_all_pdfs(chunk_size):
    """Process all PDFs in a specified directory."""

    print(f"Checking for PDFs in directory: {PDF_DIRECTORY}")
    if not os.path.exists(PDF_DIRECTORY):
        error_message = f"Error: Directory '{PDF_DIRECTORY}' does not exist."
        print(error_message)
        return {"status": "error", "message": error_message}
    
    pdf_files = [f for f in os.listdir(PDF_DIRECTORY) if f.endswith(".pdf")]
    
    if not pdf_files:
        message = f"No PDF files found. Upload one!"
        print(message)
        return {"status": "empty", "message": message}

    results = []
    for filename in pdf_files:
        pdf_path = os.path.join(PDF_DIRECTORY, filename)
        result = process_pdf(pdf_path, chunk_size)
        results.append(result)

    return {"status": "completed", "results": results}


# Run the function on your PDF
if __name__ == "__main__":
    list_all_embeddings()
    # clear_all_embeddings(reset=True)
    # clear_pdf_embeddings("pdfs/hideAndSeek.pdf")
    # process_all_pdfs()
    # chunk_text("Adjust your report depending on the KPI’s scope by clicking on the se^ngs icon(gear) on the upper right side of your screen. All KPI’s are broken down into two'major categories (Messages and Users) depending on what their data are referring to. To adjust your report according to the KPI’s scope, click on these^ngs icon (gear), select from the “View” dropdown menu your preferable op?on (Messages or User) & click on Apply. This ac?on will hide all the unrelated KPI columns.")

    # Example query
    # query = "How can i create a grow campaign?"
    # relevant_chunks = search_docs(query)

    # print("\nMost Relevant Chunks:")
    # for chunk in relevant_chunks:
    #     print("-" * 80)
    #     print(chunk)