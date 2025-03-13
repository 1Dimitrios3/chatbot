# RAG Chatbot
## Integration with OpenAI

This repository contains the code for a Retrieval-Augmented Generation (RAG) Chatbot that integrates with OpenAI. The application allows users to interact with AI using both PDF and CSV data for contextual, data-driven conversations.

## Key Features:
- **Upload PDF & CSV files:** Process and store PDF documents and structured CSV datasets.
- **Train a model:** Generate document embeddings from PDFs and vectorize CSV data for retrieval.
- **Chat with the model:** Query the trained model to receive contextually relevant responses based on the uploaded PDFs and CSV records.
- **Retrieval-Augmented Generation (RAG):** Enhances responses by fetching relevant information from uploaded documents and datasets before generating answers.
- **Streaming Responses:** Provides real-time, incremental responses from OpenAI, ensuring a faster and interactive user experience.
- **Tool Calls for CSV Analysis:** Enables advanced data querying on CSV files, including summarization, column comparisons, and statistical insights.

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

3. The project uses ChromaDB for managing pdf document embeddings and Faiss db for csv embeddings. Ensure that the CHROMA_STORAGE_PATH environment variable is set correctly to avoid stale storage issues.

4. If you encounter an issue where the chatbot is not responding properly about PDF files, try updating the CHROMA_STORAGE_PATH environment variable.

## Backend Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd <repository-directory>

2. All required Python dependencies are listed in dependencies.txt. Install them using:
   ```bash
   pip/python install -r dependencies.txt

3. Start the Backend Server locally
     ```bash
     uvicorn main:app --reload

4. You may also run the server and scripts using Docker.
      ```bash
      docker build -f Dockerfile.runServer -t chatbot_be .
      docker run -p 8000:8000 chatbot_be
      
      docker build -f Dockerfile.runScripts -t pdf_processor .
      docker run --rm pdf_processor

## Frontend Setup

1. cd tanstack_fe
   ```bash
      pnpm i 
      pnpm dev


* To view embeddings run
   ```bash
      streamlit run view_pdf_embeddings.py

## Examples

Try out different queries to interact with the chatbot effectively eg.

**PDF-Based Queries**
- What are the key takeaways from the document?
- Find sections related to [specific topic].

**CSV-Based Queries**
- Analyze x column for me.
- Show the average values for these columns.
- What are some trends you observe about the dataset?

**Generating Charts from Categorical Columns** (BETA)
If you want a pie chart visualization for a categorical column, append -> 'show piechart' to your query:

Example: 
- Analyze x column. Show piechart