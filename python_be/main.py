from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from pydantic import BaseModel
import openai
import os
from process_pdf import search_docs, process_all_pdfs
from dotenv import load_dotenv
from helpers.helpers import openai_stream_generator
from fastapi.responses import StreamingResponse

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# improve this part
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Ensure the `/pdfs` directory exists
UPLOAD_FOLDER = "./pdfs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Dictionary to store chat history per session (Temporary storage)
chat_histories = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    query = request.message
    session_id = request.session_id

    if session_id not in chat_histories:
        chat_histories[session_id] = []

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
    chat_histories[session_id] = chat_histories[session_id][-10:]

    messages.extend(chat_histories[session_id])  # ✅ Keep conversation history
    messages.append({"role": "user", "content": user_message})

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.2,
        stream=True
        # store=True # if this is added completion history/messages can be retrieved
    )

  # ✅ Save user query before streaming response
    chat_histories[session_id].append({"role": "user", "content": query})
    print('chat_histories', chat_histories)

    return StreamingResponse(
        content=openai_stream_generator(response, session_id, chat_histories),
        media_type="text/plain"
    )

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Handles PDF uploads and stores them in the /pdfs folder.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return {"message": "File uploaded successfully!", "filename": file.filename}


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

async def train_process():
    """
    Background task that runs the training process and updates status.
    """
    global TRAINING_STATUS

    TRAINING_STATUS["status"] = "running"
    TRAINING_STATUS["message"] = "Training process is in progress..."
    await send_status_updates()

    try:
        result = process_all_pdfs()

        if result["status"] == "empty":  # Handle empty directory case
            TRAINING_STATUS["status"] = "empty"
            TRAINING_STATUS["message"] = result["message"]
        else:
            TRAINING_STATUS["status"] = "completed"
            TRAINING_STATUS["message"] = "Training process completed successfully!"
            TRAINING_STATUS["details"] = result  # Include the detailed results
        
    except Exception as e:
        TRAINING_STATUS["status"] = "error"
        TRAINING_STATUS["message"] = f"Training failed: {str(e)}"

    await send_status_updates()  # Notify clients when training finishes

@app.post("/api/train")
async def train_model(background_tasks: BackgroundTasks):
    """
    Starts the training process in the background and returns immediately.
    """
    if TRAINING_STATUS["status"] == "running":
        raise HTTPException(status_code=400, detail="Training is already in progress.")

    background_tasks.add_task(asyncio.run, train_process())  # Run asynchronously
    return {"message": "Training process started in the background!"}

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