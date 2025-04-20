import os
import json
import re
import pandas as pd
import openai
import faiss
from schemas.variables import *
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Dict
import chardet
from stores.chart_store import chart_data_store

# Set display options to show all columns
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)  # Adjust width if needed

def get_csv_path() -> str:
    """
    Returns the path to a CSV file found in the /datasets folder.
    If multiple CSV files are found, returns the first one.
    Raises FileNotFoundError if no CSV file is found.
    """
    dataset_dir = "datasets"
    for file in os.listdir(dataset_dir):
        if file.endswith(".csv"):
            return os.path.join(dataset_dir, file)
    raise FileNotFoundError("No CSV file found in the datasets directory")

def detect_encoding(file_path, num_bytes=10000):
    """
    Detects the encoding of the file by reading a sample of bytes.
    """
    with open(file_path, 'rb') as f:
        raw_data = f.read(num_bytes)
    detected = chardet.detect(raw_data)
    return detected.get('encoding', 'utf-8')  # Fallback to UTF-8 if not detected

def chunk_dataframe(df: pd.DataFrame, chunk_size: int = 200, overlap: int = 3) -> list:
    """
    Splits a cleaned DataFrame into smaller overlapping JSON chunks.
    
    Each chunk contains up to `chunk_size` rows, and consecutive chunks overlap by `overlap` rows.
    
    Best Practices for Choosing chunk_size:
    - For small datasets (≤ 10K rows): chunk_size = 100 - 500 is usually fine.
    - For medium datasets (10K - 1M rows): chunk_size = 500 - 2000 may improve efficiency.
    - For very large datasets (1M+ rows): chunk_size = 5000+ is better to minimize overhead.
    
    The `overlap` value should be less than `chunk_size`.
    """
    if overlap >= chunk_size:
        raise ValueError("Overlap must be less than chunk_size.")
    
    chunks = []
    step = chunk_size - overlap  # number of rows to advance for each new chunk
    for i in range(0, len(df), step):
        chunk = df.iloc[i:i+chunk_size]
        chunks.append(chunk.to_json(orient="records"))
        print(f"Processing chunk {len(chunks)} of approx. {((len(df)-1) // step) + 1}", flush=True)
    
    return chunks

def create_embeddings_from_chunks(json_chunks: list) -> (list, list): # type: ignore
    """
    Generates embeddings from JSON chunks using OpenAI's embedding model.
    Also returns a list of text records corresponding to each embedding.
    """
    embeddings_list = []  # To store all generated embeddings
    text_records = []     # To map embeddings back to their text
    for i, json_data in enumerate(json_chunks):
        print(f"🔹 Generating embeddings for chunk {i+1} of {len(json_chunks)}", flush=True)
        # Convert JSON string to a list of dictionaries
        chunk_data = json.loads(json_data)
        
        # Build text input for each record:
        text_inputs = []
        for d in chunk_data:
            # Concatenate all key-value pairs into a single string.
            # Sorting the items ensures a consistent order.
            text = ", ".join([f"{k}: {v}" for k, v in sorted(d.items())])
            text_inputs.append(text)
        
        if not text_inputs:
            print(f"⚠️ Skipping chunk {i+1} - No valid text fields found.")
            continue

        # Generate embeddings for each text input using OpenAI's API
        try:
            chunk_embeddings = [
                openai.embeddings.create(input=text, model="text-embedding-ada-002").data[0].embedding
                for text in text_inputs
            ]
        except Exception as e:
            print(f"Error generating embeddings for chunk {i+1}: {e}")
            continue

        embeddings_list.extend(chunk_embeddings)
        text_records.extend(text_inputs)

    print(f"✅ Successfully generated {len(embeddings_list)} embeddings.", flush=True)
    return embeddings_list, text_records

def build_faiss_index(embeddings_list: list):
    """
    Builds a FAISS flat (L2) index from a list of embeddings.
    Returns the FAISS index.
    """
    embeddings_np = np.array(embeddings_list).astype('float32')
    if embeddings_np.ndim < 2:
        raise ValueError("No embeddings were generated. Please check your data and text extraction.")
    
    dim = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings_np)
    print(f"✅ FAISS index built with {index.ntotal} embeddings.")
    return index

def reset_faiss_index():
    """
    Deletes the stored FAISS index and text records file, allowing for a fresh start.
    """
    if os.path.exists(INDEX_FILE):
        os.remove(INDEX_FILE)
        print(f"Deleted FAISS index file: {INDEX_FILE}")
    else:
        print(f"FAISS index file not found: {INDEX_FILE}")
    
    if os.path.exists(TEXT_RECORDS_FILE):
        os.remove(TEXT_RECORDS_FILE)
        print(f"Deleted text records file: {TEXT_RECORDS_FILE}")
    else:
        print(f"Text records file not found: {TEXT_RECORDS_FILE}")
        
def prepare_clean_data(csv_path: str, encoding: str = "utf-8") -> pd.DataFrame:
    """
    Reads a CSV file, cleans the data by removing duplicates and missing values,
    and returns a cleaned DataFrame.
    """
    df = pd.read_csv(csv_path, encoding=encoding)
    df.drop_duplicates(inplace=True)
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def clean_df_text(df):
     # Convert column labels to strings before cleaning
     df.columns = df.columns.astype(str).str.lower()
     df.columns = df.columns.astype(str).str.strip()

     # clean row values of object columns
     for column in df.columns:
         if df[column].dtype == 'object':
             df[column] = df[column].str.title()
             df[column] = df[column].str.strip()

     return df


def get_min_max_mean(csv_path, encoding: str = "utf-8"):
     df = pd.read_csv(csv_path, encoding=encoding)
     results = clean_df_text(df)
     numeric_summary = results.describe().loc[['min', 'max', 'mean']]

     return numeric_summary


# Get the summary
# summary_stats = get_min_max_mean(csv_path)
# print('summary_stats', summary_stats)

# print("Summary Statistics (min, max, mean) for each column:")
# print(summary_stats)

def get_totals(csv_path, encoding: str = "utf-8"):
     df = pd.read_csv(csv_path, encoding=encoding)
     # Clean the DataFrame first
     df = clean_df_text(df)

     # Calculate totals for each numeric column
     totals = df.select_dtypes(include=['number']).sum()
     return totals

# Get and print the totals for each numeric column
# totals = get_totals(csv_path)
# print("Totals for each numeric column:")
# print(totals)

def create_category_aggregates(csv_path: str, encoding: str = "utf-8",  column_of_interest: str = None):
     """
     Computes a set of aggregates for each column.

     column_of_interest -> we need this argument even if not used for llm inference via tool

     For numeric columns, computes:
       - Count, Missing Count, Sum, Mean, Median, Std, Variance, Min,
         25th, 50th, 75th percentiles, and Max.

     For categorical columns, computes:
       - Count, Missing Count, Unique Count, Mode,
         Top 3 most frequent values and their frequencies,
         Lowest 3 least frequent values and their frequencies.
     """
     df = pd.read_csv(csv_path, encoding=encoding)
     df = clean_df_text(df)

     numeric_cols = df.select_dtypes(include=['number']).columns
     categorical_cols = df.select_dtypes(exclude=['number']).columns

     numeric_metrics = {}
     for col in numeric_cols:
         s = df[col]
         numeric_metrics[col] = {
             'Count': s.count(),
             'Missing': s.isna().sum(),
             'Sum': s.sum(),
             'Mean': s.mean(),
             'Median': s.median(),
             'Std': s.std(),
             'Variance': s.var(),
             'Min': s.min(),
             '25%': s.quantile(0.25),
             '50%': s.quantile(0.50),
             '75%': s.quantile(0.75),
             'Max': s.max(),
             'Range': s.max() - s.min() if s.count() > 0 else None
         }

     categorical_metrics = {}
     for col in categorical_cols:
         s = df[col]
         counts = s.value_counts()
         top_counts = counts.head(3)
         low_counts = counts.sort_values(ascending=True).head(3)

         cat_data = {
             'Count': s.count(),
             'Missing': s.isna().sum(),
             'Unique': s.nunique(),
             'Mode': s.mode().iloc[0] if not s.mode().empty else None,
         }

         # Top 3 values: frequencies and relative percentages.
         for i in range(1, 4):
            value = top_counts.index[i-1] if i <= len(top_counts) else None
            frequency = top_counts.iloc[i-1] if i <= len(top_counts) else None
            percentage = (frequency / s.count() * 100) if frequency is not None else None
            cat_data[f'Top{i}'] = value
            cat_data[f'Top_Frequency{i}'] = frequency
            cat_data[f'Top_Percentage{i}'] = round(percentage, 2) if percentage is not None else None

         # Lowest 3 values: frequencies and relative percentages.
         for i in range(1, 4):
            value = low_counts.index[i-1] if i <= len(low_counts) else None
            frequency = low_counts.iloc[i-1] if i <= len(low_counts) else None
            percentage = (frequency / s.count() * 100) if frequency is not None else None
            cat_data[f'Low{i}'] = value
            cat_data[f'Low_Frequency{i}'] = frequency
            cat_data[f'Low_Percentage{i}'] = round(percentage, 2) if percentage is not None else None

         categorical_metrics[col] = cat_data

     numeric_df = pd.DataFrame(numeric_metrics).T
     categorical_df = pd.DataFrame(categorical_metrics).T
     return numeric_df, categorical_df

# Generate aggregates
# numeric_aggregates, categorical_aggregates = create_category_aggregates(csv_path)

# print("Numeric Aggregates:")
# print(numeric_aggregates)

# print("\nCategorical Aggregates:")
# print(categorical_aggregates)

def find_column(df_columns, query_col):
    """
    Given a list of columns and a query column name, returns the first column
    that contains the query as a substring.
    """
    # Try exact match first.
    if query_col in df_columns:
        return query_col
    # Else try substring matching.
    for col in df_columns:
        if query_col in col:
            return col
    return None

def compare_columns(csv_path: str, column1: str, column2: str, encoding='utf-8') -> str:
    """
    Compares two columns in the dataset by performing a cross-tabulation.
    Returns the result as a formatted string.
    """
    df = pd.read_csv(csv_path, encoding=encoding)
    # Normalize column names.
    df.columns = df.columns.str.strip().str.lower()
    normalized_col1 = column1.strip().lower()
    normalized_col2 = column2.strip().lower()

    col1_actual = find_column(df.columns, normalized_col1)
    col2_actual = find_column(df.columns, normalized_col2)

    if not col1_actual or not col2_actual:
        return (
            f"Error: Could not find one or both columns ('{column1}', '{column2}'). "
            f"Available columns: {df.columns.tolist()}"
        )

    comparison = pd.crosstab(df[col1_actual], df[col2_actual])
    return comparison.to_string()

async def stream_openai_response(response_iterator):
    """
    Simple streaming helper that yields OpenAI response chunks.
    """
    for chunk in response_iterator:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content

def generate_pie_chart_data(csv_path: str, encoding: str = "utf-8", column_of_interest: Optional[str] = None, session_id: Optional[str] = None) -> Optional[Dict]:
    """
    Generates pie chart data from a CSV file for a given column if it is categorical.
    
    For a categorical column, it computes the frequency distribution of each category.
    
    Parameters:
        csv_path (str): The path to the CSV file.
        column_of_interest (Optional[str]): The name of the column to analyze.
        session_id (Optional[str]): If provided, the chart data is stored in the global chart_data_store under this session ID.
        
    Returns:
        Optional[Dict]: A dictionary with a "pie_chart" key containing "labels" and "values",
                        or None if the conditions are not met.
    """
    # Clear any previously stored chart data for this session.
    if session_id is not None and session_id in chart_data_store:
        chart_data_store.pop(session_id)
    
    # Read and clean the CSV file.
    df = pd.read_csv(csv_path, encoding=encoding)
    df = clean_df_text(df)  # Use your cleaning function if needed.

    if column_of_interest:
        # Normalize the column name for case-insensitive comparison.
        column_norm = column_of_interest.strip().lower()
        df_columns_norm = [col.strip().lower() for col in df.columns]
        
        # Try for an exact match first.
        if column_norm in df_columns_norm:
            matched_col = df.columns[df_columns_norm.index(column_norm)]
        else:
            # If no exact match, try substring matching.
            matched_col = None
            for original, norm in zip(df.columns, df_columns_norm):
                if column_norm in norm:
                    matched_col = original
                    break
                    
        if matched_col:
            # Check if the column is categorical (i.e. not numeric).
            if not pd.api.types.is_numeric_dtype(df[matched_col]):
                distribution = df[matched_col].value_counts()
                labels = distribution.index.tolist()   # e.g., ["Mobile", "Laptop", "Tablet", "Smart TV"]
                values = distribution.tolist()           # e.g., [2, 2, 2, 3]
                
                chart_data = {
                    "pie_chart": {
                        "labels": labels,
                        "values": values
                    }
                }
                
                if session_id is not None:
                    chart_data_store[session_id] = chart_data
                    
                return chart_data
            else:
                print(f"Column '{matched_col}' is numeric. Pie chart generation is only allowed for categorical columns.")
                # Clear any previous chart data for this session.
                if session_id in chart_data_store:
                    chart_data_store.pop(session_id)
        else:
            print("No matching column found. column_of_interest_norm:", column_norm)
            print("Normalized DataFrame columns:", df_columns_norm)
    else:
        print("No column_of_interest provided; cannot generate chart data.")
    
    return None


def should_show_piechart(query: str) -> bool:
    # This regex checks (case-insensitively) that the query contains both "show" and "pie chart" or "piechart"
    pattern = re.compile(r'(?i)(?=.*\bshow\b)(?=.*\bpie[\s-]?chart\b)')
    return bool(pattern.search(query))

def should_show_barchart(query: str) -> bool:
    """
    Determines if the query indicates a bar chart should be shown.
    
    The regex below checks (case-insensitively) that the query contains the word "show"
    and one of the following variations:
      - "bar chart"
      - "bar-chart"
      - "bar graph"
      - "bar-graph"
      - "bargraph"
    """
    pattern = re.compile(
        r'(?i)(?=.*\bshow\b)(?=.*\bbar(?:[\s-]*(?:chart|graph))\b)'
    )
    return bool(pattern.search(query))

def generate_bar_chart_data_for_numeric_summary(csv_path: str, session_id: Optional[str] = None) -> Optional[Dict]:
    """
    Generates bar chart data for a grouped bar chart visualization from numeric summary statistics.
    
    This chart shows min, max, and mean values for each numeric column in the CSV file.
    
    Parameters:
        csv_path (str): The path to the CSV file.
        session_id (Optional[str]): Optional session identifier to store the chart data.
    
    Returns:
        Optional[Dict]: A dictionary formatted for Chart.js containing labels and datasets,
                        or None if an error occurs.
    """
    try:
        # Get the numeric summary DataFrame from get_min_max_mean
        numeric_summary = get_min_max_mean(csv_path)
        
        # Prepare the labels (column names) for the chart.
        labels = list(numeric_summary.columns)
        
        # Define colors for each statistic.
        colors = {
            'min': 'rgba(255, 99, 132, 0.6)',
            'max': 'rgba(54, 162, 235, 0.6)',
            'mean': 'rgba(255, 206, 86, 0.6)'
        }
        
        # Create datasets for each statistic.
        datasets = []
        for stat in ['min', 'max', 'mean']:
            if stat in numeric_summary.index:
                dataset = {
                    "label": stat.capitalize(),
                    "data": numeric_summary.loc[stat].tolist(),
                    "backgroundColor": colors[stat]
                }
                datasets.append(dataset)
        
        # Construct the chart data in the format expected by Chart.js.
        chart_data = {
            "bar_chart": {
                "labels": labels,
                "datasets": datasets
            }
        }
        
        # Optionally store the chart data in a global chart_data_store if session_id is provided.
        if session_id is not None:
            chart_data_store[session_id] = chart_data
        
        return chart_data
    except Exception as e:
        print("Error generating bar chart data:", str(e))
        return None
