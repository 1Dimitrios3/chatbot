import openai
import json
import numpy as np
from helpers.csv.helpers import *
from schemas.variables import *
from schemas.tools import tools
from fastapi import HTTPException
from helpers.csv.helpers import stream_openai_response

async def augment_summary_with_description(summary, query: str, model: str):
    """
    Calls the LLM in streaming mode to provide a concise explanation of the summary.
    Yields chunks as they are received.
    """
    # Convert to string if needed.
    summary_str = summary.to_string() if hasattr(summary, "to_string") else str(summary)
    
    prompt = (
        "Below is a summary table showing key statistics for a dataset (provided for context only):\n"
        f"{summary_str}\n\n"
        "Based on the above data, please provide a concise explanation of the key insights. "
        "Do NOT include the raw table data in your response. "
        "Only include the raw table data if the user explicitly requests it (for example, using phrases like 'raw data' or 'raw table').\n\n"
        f"User Query: {query}\n"
        "Your explanation:"
    )
    
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": (
                "You are a helpful data analysis assistant. When providing insights based on summary tables, "
                "offer a concise explanation without including the raw table data unless explicitly requested by the user."
            )},
            {"role": "user", "content": prompt}
        ],
        stream=True,
        temperature=0.3
    )
    
    async for chunk in stream_openai_response(response):
        yield chunk

async def explain_comparison(comparison_result: str, column1: str, column2: str, query: str, model: str):
    """
    Streams a concise explanation comparing two columns based on cross-tabulated data.
    Yields chunks as they are received.
    """
    prompt = (
        f"Below is a cross-tabulation between the '{column1}' and '{column2}' columns of a dataset.\n"
        "Use this data to provide a concise explanation comparing the two columns in terms of frequency, patterns, or relationships.\n"
        "Do NOT output the raw cross-tabulated data; only provide a summary explanation that accurately answers the query.\n"
        f"User Query: {query}\n"
        f"Cross-Tabulation Data:\n{comparison_result}\n"
        "Your explanation:"
    )
    
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": (
                "You are a helpful data analysis assistant. When comparing two dataset columns, provide a concise, insightful explanation of the relationship between the columns. "
                "Do not include the raw cross-tabulation data in your final response."
            )},
            {"role": "user", "content": prompt}
        ],
        stream=True,
        temperature=0.3
    )
    
    async for chunk in stream_openai_response(response):
        yield chunk


# Global conversation memory for CSV chat
csv_chat_history = {}

async def ask_question_about_dataset(
    selected_chunks: list, 
    query: str, 
    session_id: str, 
    model: str = "gpt-4o-mini", 
    temperature: float = 0.3
):
    """
    Builds the prompt by combining system instructions, conversation history, and the current query.
    Then it calls OpenAI's ChatCompletion API (with tool support) and yields the answer.
    Updates the conversation memory with both the user query and assistant's answer.
    """
    # Build context from selected chunks.
    context = "\n\n".join(selected_chunks)
    
    # Define the system instructions.
    system_message = {
        "role": "system",
        "content": (
            "You are a helpful assistant. When you receive queries that ask about trends—such as which category is used most or least often, "
            "or questions regarding frequency or averages—first use the available functions (like get_min_max_mean and create_category_aggregates) "
            "to retrieve data from the CSV file, then base your answer solely on that data. "
            "Do not include raw table data in your final answer unless the user explicitly requests it."
        )
    }
    
    # Build the user message.
    user_message = {
        "role": "user",
        "content": f"Answer the following query based on the provided text:\n\n{context}\n\nQuery: {query}\nAnswer:"
    }
    
    # Retrieve the existing history for this session (limit to the last 10 messages).
    history = csv_chat_history.get(session_id, [])[-10:]
    
    # Build the full messages payload.
    messages = [system_message] + history + [user_message]
    
    # Append the current user query to the conversation history.
    csv_chat_history.setdefault(session_id, []).append({"role": "user", "content": query})
    
    # Make the initial (synchronous) call to OpenAI.
    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature, # not supported in o series reasoning models
        tools=tools  # Pass tool configuration if needed.
    )
    
    full_response = ""
    
    # If a tool call exists, process it and stream the follow-up response.
    if response.choices[0].message.tool_calls:
        try:
            tool_call = response.choices[0].message.tool_calls[0]
            print('tool_call ->', tool_call)
            function_name = tool_call.function.name
            arguments_json = tool_call.function.arguments
            arguments = json.loads(arguments_json)
            if arguments.get("csv_path"):
                arguments["csv_path"] = get_csv_path()
            
            # Based on the tool call, stream the follow-up answer.
            if function_name == "get_min_max_mean":
                res = get_min_max_mean(**arguments)
                async for subchunk in augment_summary_with_description(res, query, model):
                    full_response += subchunk
                    yield subchunk
            elif function_name == "create_category_aggregates":
                res = create_category_aggregates(**arguments)
                async for subchunk in augment_summary_with_description(res[1], query, model):
                    full_response += subchunk
                    yield subchunk
            elif function_name == "compare_columns":
                res = compare_columns(**arguments)
                async for subchunk in explain_comparison(res, arguments["column1"], arguments["column2"], query, model):
                    full_response += subchunk
                    yield subchunk
            else:
                yield "Unknown function called."
        except Exception as e:
            yield f"Error processing tool call: {str(e)}"
    else:
        # No tool call; yield the full answer directly.
        answer = response.choices[0].message.content
        full_response = answer
        yield answer
    
    # Update chat history with the assistant's answer.
    csv_chat_history[session_id].append({"role": "assistant", "content": full_response})
    # Optionally, limit the history to a maximum number of messages (e.g., last 12 entries).
    csv_chat_history[session_id] = csv_chat_history[session_id][-12:]



def process_csv(csv_path):
    """
    Processes the uploaded CSV file for training by ensuring that the FAISS index and associated text records are ready.
    If the CSV file has already been processed (i.e., the FAISS index and text records exist), it loads them and returns a flat
    response indicating that the CSV was skipped. Otherwise, it cleans the CSV data, chunks it, generates embeddings, builds a new
    FAISS index, and saves the results.

    Returns a dictionary with:
      - "status": "skipped", "processed", or "error"
      - "message": A descriptive message about the processing outcome.
    """
    filename = os.path.basename(csv_path)

    if os.path.exists(INDEX_FILE) and os.path.exists(TEXT_RECORDS_FILE):
        print("\n🔹 Loading existing FAISS Index and text records...")
        # Load index and records (for internal use) but do not return them in this function.
        faiss_index = faiss.read_index(INDEX_FILE)
        with open(TEXT_RECORDS_FILE, "r") as f:
            text_records = json.load(f)
        print(f"✅ FAISS index loaded with {faiss_index.ntotal} embeddings.")
        message = f"✅ Skipping {filename}: Already processed."
        return {"status": "skipped", "message": message}
    else:
        print("\n🔹 Cleaning Data...")
        clean_df = prepare_clean_data(csv_path)
        print(f"✅ Cleaned DataFrame with {len(clean_df)} rows.")
    
        print("\n🔹 Chunking Data...")
        json_chunks = chunk_dataframe(clean_df, chunk_size=300)
        print(f"✅ Created {len(json_chunks)} chunks.")
    
        print("\n🔹 Generating Embeddings and text records...")
        embeddings, text_records = create_embeddings_from_chunks(json_chunks)
        print(f"✅ Total Embeddings Created: {len(embeddings)}")
    
        print("\n🔹 Building FAISS Index...")
        try:
            faiss_index = build_faiss_index(embeddings)
            print(f"✅ FAISS index now contains {faiss_index.ntotal} embeddings.")
            # Save the index and text records for future runs
            faiss.write_index(faiss_index, INDEX_FILE)
            print(f"✅ FAISS index saved to {INDEX_FILE}")
            with open(TEXT_RECORDS_FILE, "w") as f:
                json.dump(text_records, f)
            print(f"✅ Text records saved to {TEXT_RECORDS_FILE}")
        except Exception as ve:
            error_message = f"Error building FAISS index: {ve}"
            print(error_message)
            return {"status": "error", "message": error_message}
    
    message = f"CSV {filename} successfully processed!"
    return {"status": "processed", "message": message}

def process_all_csvs():
    """Process all CSV files in a specified directory.
        Currently we process only a single csv.
        We keep this function in case this changes in the future.
    """
    print(f"Checking for CSVs in directory: {CSV_DIRECTORY}")
    if not os.path.exists(CSV_DIRECTORY):
        error_message = f"Error: Directory '{CSV_DIRECTORY}' does not exist."
        print(error_message)
        return {"status": "error", "message": error_message}
    
    csv_files = [f for f in os.listdir(CSV_DIRECTORY) if f.endswith(".csv")]
    
    if not csv_files:
        message = "No CSV files found. Upload one!"
        print(message)
        return {"status": "empty", "message": message}
    
    results = []
    for filename in csv_files:
        csv_path = os.path.join(CSV_DIRECTORY, filename)
        result = process_csv(csv_path)
        results.append(result)
  
    return {"status": "completed", "results": results}

def get_csv_index_records():
    """
    Retrieves the FAISS index and text records for the CSV file.
    Raises an HTTPException if either file does not exist, indicating that 
    CSV processing has not been completed yet.
    
    Returns:
        Tuple[faiss.Index, List[str]]: The loaded FAISS index and text records.
    """
    if not (os.path.exists(INDEX_FILE) and os.path.exists(TEXT_RECORDS_FILE)):
        raise HTTPException(
            status_code=400, 
            detail="CSV not processed yet. Please process the CSV file first."
        )
    
    faiss_index = faiss.read_index(INDEX_FILE)
    with open(TEXT_RECORDS_FILE, "r") as f:
        text_records = json.load(f)

    return faiss_index, text_records
        
def process_query(query_text: str, faiss_index, k: int = 5):
    """
    Processes the input query by generating its embedding and performing a similarity search 
    against the provided FAISS index. Returns the top k nearest neighbor indices and distances.
    """
    try:
        response = openai.embeddings.create(input=query_text, model="text-embedding-ada-002")
        query_embedding = response.data[0].embedding
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        return None, None

    query_embedding_np = np.array(query_embedding).astype('float32').reshape(1, -1)
    distances, indices = faiss_index.search(query_embedding_np, k)
    return distances, indices


