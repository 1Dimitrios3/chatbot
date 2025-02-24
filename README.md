# RAG Chatbot
## Integration with OpenAI

This repository contains the code for a Retrieval-Augmented Generation (RAG) Chatbot that integrates with OpenAI. This application provides the ability to:
- **Upload PDF files:** Process and store PDF documents.
- **Train a model:** Generate document embeddings from the PDFs.
- **Chat with the model:** Query the trained model to receive contextually relevant responses based on the uploaded documents.

The project is split into two parts:
- A **FastAPI-based backend** that handles PDF processing, training, and chat interactions.
- A **TanStack Router frontend** that provides the user interface for interacting with the chatbot.

---

## Environment Configuration

To configure where embeddings are stored and to provide your OpenAI API key, set the following environment variables:

1. Create a `.env` file in the backend root directory with the following content:
   ```env
   CHROMA_STORAGE_PATH=./chroma_storage
   OPENAI_API_KEY=your_api_key_here

2. Alternatively, you can input your OpenAI API key via the /enterKey route on the app.

3. The project uses ChromaDB for managing document embeddings. Ensure that the CHROMA_STORAGE_PATH environment variable is set correctly to avoid stale storage issues.

## Backend Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd <repository-directory>

2. All required Python dependencies are listed in dependencies.txt. Install them using:

-> pip/python install -r dependencies.txt

3. Start the Backend Server locally

Run the FastAPI server using Uvicorn:

-> uvicorn main:app --reload

# You can also run the server and scripts using Docker.

Start the Backend Server with Docker:

-> docker build -f Dockerfile.runServer -t chatbot_be .

-> docker run -p 8000:8000 chatbot_be

Run Processing Scripts with Docker:

-> docker build -f Dockerfile.runScripts -t pdf_processor .

-> docker run --rm pdf_processor

## Frontend Setup

cd tanstack_fe

run 

pnpm i 

pnpm dev


* To view embeddings run 
-> streamlit run view_embeddings.py
