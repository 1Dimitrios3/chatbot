import os
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Body, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from pydantic import BaseModel
import openai
from processors.pdf.process_pdf import search_docs, process_all_pdfs
from dotenv import load_dotenv
from helpers.csv.helpers import *
from schemas.variables import *
from helpers.pdf.helpers import openai_stream_generator, clear_pdf_embeddings
from fastapi.responses import StreamingResponse
from processors.csv.process_csv import process_all_csvs, get_csv_index_records, process_query, ask_question_about_dataset
from typing import List
from stores.chart_store import chart_data_store
from fastapi.responses import JSONResponse

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# improve this part
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Ensure the `/pdfs` directory exists
os.makedirs(PDF_UPLOAD_FOLDER, exist_ok=True)

# Ensure the `/datasets` directory exists
os.makedirs(CSV_UPLOAD_FOLDER, exist_ok=True)

# Dictionary to store chat history per session (Temporary storage)
pdf_chat_history = {}

async def reset_training_status():
    global TRAINING_STATUS
    TRAINING_STATUS.clear()
    TRAINING_STATUS.update({"status": "idle", "message": ""})
    await send_status_updates()

class ChatRequest(BaseModel):
    message: str
    session_id: str
    model: str

@app.post("/api/pdf/chat")
async def chat_pdf_endpoint(request: ChatRequest):
    query = request.message
    session_id = request.session_id
    selectedModel = request.model

    if session_id not in pdf_chat_history:
        pdf_chat_history[session_id] = []

    # Retrieve relevant documents from ChromaDB
    retrieved_docs = search_docs(query)
    context = "\n".join(retrieved_docs)

     # Build the base system instructions
    if context.strip():
        # When there is context, instruct the assistant to strictly answer from it.
        system_messages = [
            {
                "role": "system",
                "content": "You are an AI assistant that provides answers based solely on the provided PDF."
            },
            {
                "role": "system",
                "content": "Do not answer outside the given documents. If no relevant information is found, say: 'I am sorry. I don't have knowledge over what you ask.'"
            }
        ]
        user_message = f"User query: {query}\n\nRelevant documents:\n{context}"
    else:
        # When no context is available, change the instructions.
        system_messages = [
            {
                "role": "system",
                "content": ("You are an AI assistant. Currently, there is no context provided from any documents. "
                            "Instead of answering with a default apology, instruct the user to train you on the subject. "
                            "For example, say: 'I don't have any context to answer this query. Please provide training materials on this topic and try again.'")
            }
        ]
        user_message = f"User query: {query}\n\nNo relevant documents found."

    # Start building the messages list with system instructions and history.
    messages = system_messages
    
    # Keep only the last 10 messages
    pdf_chat_history[session_id] = pdf_chat_history[session_id][-10:]

    messages.extend(pdf_chat_history[session_id])  # ✅ Keep conversation history
    messages.append({"role": "user", "content": user_message})

    response = openai.chat.completions.create(
        model=selectedModel if selectedModel else "gpt-4o-mini",
        messages=messages,
        temperature=0.3,
        stream=True
        # store=True # if this is added completion history/messages can be retrieved
    )

  # ✅ Save user query before streaming response
    pdf_chat_history[session_id].append({"role": "user", "content": query})
    print('pdf_chat_history', pdf_chat_history)

    return StreamingResponse(
        content=openai_stream_generator(response, session_id, pdf_chat_history),
        media_type="text/plain"
    )

@app.post("/api/pdf/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Handles PDF uploads and stores them in the /pdfs folder.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    # Check how many PDFs are already in the folder
    try:
        files = os.listdir(PDF_UPLOAD_FOLDER)
        pdf_files = [f for f in files if f.endswith(".pdf")]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if len(pdf_files) >= 5:
        raise HTTPException(status_code=400, detail="Maximum of 5 PDFs allowed.")


    file_path = os.path.join(PDF_UPLOAD_FOLDER, file.filename)

    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    await reset_training_status()

    return {"message": "File uploaded successfully!", "filename": file.filename}

@app.get("/api/pdf/list", response_model=List[str])
async def list_pdfs():
    """
    Lists all PDFs available in the upload folder.
    """
    try:
        files = os.listdir(PDF_UPLOAD_FOLDER)
        # Filter for files ending with .pdf
        pdf_files = [f for f in files if f.endswith(".pdf")]
        return pdf_files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/pdf/delete")
async def delete_pdf(filename: str = Query(..., description="Name of the PDF file to delete")):
    """
    Deletes a PDF file by name from the upload folder.
    """
    # Use os.path.basename to prevent directory traversal attacks
    safe_filename = os.path.basename(filename)
    if not safe_filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file name provided. Must be a .pdf file.")
    
    file_path = os.path.join(PDF_UPLOAD_FOLDER, safe_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    
    # Clear embeddings associated with the PDF.
    try:
        clear_pdf_embeddings(file_path)
    except Exception as e:
        # Log the error. Optionally, you can raise an HTTPException if failing to clear embeddings should block deletion.
        print(f"Error clearing embeddings for {file_path}: {e}")
    
    # Delete the PDF file from storage.
    try:
        os.remove(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    await reset_training_status()
    
    return {"message": "File deleted successfully!", "filename": safe_filename}

# Global variables to track training status and WebSocket clients
TRAINING_STATUS = {"status": "idle", "message": ""}
websocket_clients = set()

async def send_status_updates():
    """Broadcasts the latest status to all connected WebSocket clients."""
    for ws in websocket_clients.copy():
        try:
            await ws.send_json(TRAINING_STATUS)
        except Exception:
            websocket_clients.discard(ws)  # Remove disconnected clients

async def train_process(file_type: str, chunk_size: int = 200):
    """
    Background task that runs the training process for either PDF or CSV files.
    """
    global TRAINING_STATUS

    TRAINING_STATUS["status"] = "running"
    TRAINING_STATUS["message"] = f"Training process for {file_type.upper()} is in progress..."
    await send_status_updates()

    try:
        if file_type.lower() == "pdf":
            result = await asyncio.to_thread(process_all_pdfs, chunk_size)
        elif file_type.lower() == "csv":
            result = await asyncio.to_thread(process_all_csvs, chunk_size)  
        else:
            raise ValueError("Invalid file type provided. Allowed values are 'pdf' or 'csv'.")
        
        if result["status"] == "empty":  # Handle empty directory case
            TRAINING_STATUS["status"] = "empty"
            TRAINING_STATUS["message"] = result["message"]
        else:
            TRAINING_STATUS["status"] = "completed"
            TRAINING_STATUS["message"] = f"Training process for {file_type.upper()} completed successfully!"
            TRAINING_STATUS["details"] = result  # Include detailed results
    except Exception as e:
        TRAINING_STATUS["status"] = "error"
        TRAINING_STATUS["message"] = f"Training failed: {str(e)}"
    finally:
        await send_status_updates()  # Send once the process has finished


@app.post("/api/train")
async def train_model(
    file_type: str = Query("pdf", description="Type of file to train on: 'pdf' or 'csv'"),
    chunk_size: str = Query("200", description="Chunk size for processing (use non-positive value for default)"),
    background_tasks: BackgroundTasks = None,
):
    if TRAINING_STATUS["status"] == "running":
        raise HTTPException(status_code=400, detail="Training is already in progress.")

    try:
        cs = int(chunk_size)
    except ValueError:
        cs = 0  # Use default if conversion fails

    if cs <= 0:
        background_tasks.add_task(train_process, file_type)
        msg = f"Training process for {file_type.upper()} with default chunk size started in the background!"
    else:
        background_tasks.add_task(train_process, file_type, chunk_size=cs)
        msg = f"Training process for {file_type.upper()} with chunk size {cs} started in the background!"

    return {"message": msg}

@app.get("/api/train/status")
async def get_training_status():
    """
    Returns the current status of the training process.
    """
    return TRAINING_STATUS

@app.websocket("/api/train/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for live training updates.
    """
    await websocket.accept()
    websocket_clients.add(websocket)

    await websocket.send_json(TRAINING_STATUS)
    try:
        while True:
            await asyncio.sleep(1)  # Keep the connection alive
    except WebSocketDisconnect:
        websocket_clients.discard(websocket)  # Remove disconnected clients

@app.post("/api/input/key")
async def set_api_key(api_key: str = Body(..., embed=True)):
    """
    Accepts an API key from the front end and stores it in the .env file 
    under the name OPENAI_API_KEY. If the key already exists, its value is updated.
    """
    env_file = ".env"

    try:
        # If .env exists, update the key if it exists or append if not
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                lines = f.readlines()

            key_found = False
            new_lines = []
            for line in lines:
                if line.startswith("OPENAI_API_KEY="):
                    new_lines.append(f"OPENAI_API_KEY={api_key}\n")
                    key_found = True
                else:
                    new_lines.append(line)

            if not key_found:
                new_lines.append(f"OPENAI_API_KEY={api_key}\n")

            with open(env_file, "w") as f:
                f.writelines(new_lines)
        else:
            # Create .env and write the API key
            with open(env_file, "w") as f:
                f.write(f"OPENAI_API_KEY={api_key}\n")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing to .env: {str(e)}")

    return {"message": "API key saved successfully!"}

@app.post("/api/csv/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Handles CSV uploads and stores them in the /datasets folder.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    # Check how many CSVs are already in the folder
    try:
        files = os.listdir(CSV_UPLOAD_FOLDER)
        csv_files = [f for f in files if f.endswith(".csv")]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if len(csv_files) >= 1:
        raise HTTPException(status_code=400, detail="Maximum of 1 CSV file is allowed.")

    file_path = os.path.join(CSV_UPLOAD_FOLDER, file.filename)

    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    await reset_training_status()

    return {"message": "File uploaded successfully!", "filename": file.filename}

@app.get("/api/csv/list", response_model=List[str])
async def list_csvs():
    """
    Lists all CSV files available in the upload folder.
    """
    try:
        files = os.listdir(CSV_UPLOAD_FOLDER)
        csv_files = [f for f in files if f.endswith(".csv")]
        return csv_files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/csv/delete")
async def delete_csv(filename: str = Query(..., description="Name of the CSV file to delete")):
    """
    Deletes a CSV file by name from the upload folder.
    """
    safe_filename = os.path.basename(filename)
    if not safe_filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file name provided. Must be a .csv file.")
    
    file_path = os.path.join(CSV_UPLOAD_FOLDER, safe_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    
    # Clear embeddings associated with the CSV.
    try:
        reset_faiss_index()
    except Exception as e:
        # Log the error. Optionally, raise an HTTPException if needed.
        print(f"Error resseting faiss index: {e}")
    
    # Delete the CSV file from storage.
    try:
        os.remove(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    await reset_training_status()
    
    return {"message": "File deleted successfully!", "filename": safe_filename} 

@app.post("/api/csv/chat")
async def chat_csv_endpoint(request: ChatRequest):
    """
    Answers a chat query using the stored FAISS index and text records in streaming mode.
    """
    session_id = request.session_id
    selected_model = request.model or "gpt-4o-mini"
    query = request.message

    # Load the FAISS index and text records
    faiss_index, text_records = get_csv_index_records()

    # Perform vector search to find top matching chunks
    distances, indices = process_query(query, faiss_index, k=5)
    if distances is None or indices is None:
        raise HTTPException(status_code=500, detail="Error processing query.")

    # Debug output: print similar results
    print("Top similar results from vector search:")
    for rank, (idx, dist) in enumerate(zip(indices[0], distances[0]), start=1):
        print(f"{rank}. Index: {idx}, Distance: {dist}")

    # Extract corresponding text chunks based on FAISS indices
    selected_chunks = [text_records[i] for i in indices[0]]

    # Use the streaming version of ask_question_about_dataset
    stream_generator = ask_question_about_dataset(selected_chunks, query, session_id, model=selected_model)
    
    return StreamingResponse(stream_generator, media_type="text/plain")

@app.get("/api/csv/chart-data/{session_id}")
async def get_chart_data(session_id: str):
    """
    Retrieves stored chart data (numeric and categorical) for a given session.
    """
    chart_data = chart_data_store.get(session_id)
    
    if not chart_data:
        return JSONResponse(content={"detail": "Chart data not found for this session."}, status_code=200)
    
    return JSONResponse(content=chart_data)