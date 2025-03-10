import os
import json
import re
import pandas as pd
import openai
import faiss
from schemas.variables import *
import numpy as np
import matplotlib.pyplot as plt

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

def chunk_dataframe(df: pd.DataFrame, chunk_size: int = 200, overlap: int = 20) -> list:
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
        print(f"Processing chunk {len(chunks)} of approx. {((len(df)-1) // step) + 1}")
    
    return chunks

def create_embeddings_from_chunks(json_chunks: list) -> (list, list): # type: ignore
    """
    Generates embeddings from JSON chunks using OpenAI's embedding model.
    Also returns a list of text records corresponding to each embedding.
    """
    embeddings_list = []  # To store all generated embeddings
    text_records = []     # To map embeddings back to their text
    for i, json_data in enumerate(json_chunks):
        print(f"🔹 Generating embeddings for chunk {i+1} of {len(json_chunks)}")
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

    print(f"✅ Successfully generated {len(embeddings_list)} embeddings.")
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
        
def prepare_clean_data(csv_path: str) -> pd.DataFrame:
    """
    Reads a CSV file, cleans the data by removing duplicates and missing values,
    and returns a cleaned DataFrame.
    """
    df = pd.read_csv(csv_path)
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


def get_min_max_mean(csv_path):
     df = pd.read_csv(csv_path)
     results = clean_df_text(df)
     numeric_summary = results.describe().loc[['min', 'max', 'mean']]

     return numeric_summary


# Get the summary
# summary_stats = get_min_max_mean(csv_path)
# print('summary_stats', summary_stats)

# print("Summary Statistics (min, max, mean) for each column:")
# print(summary_stats)

def get_totals(csv_path):
     df = pd.read_csv(csv_path)
     # Clean the DataFrame first
     df = clean_df_text(df)

     # Calculate totals for each numeric column
     totals = df.select_dtypes(include=['number']).sum()
     return totals

# Get and print the totals for each numeric column
# totals = get_totals(csv_path)
# print("Totals for each numeric column:")
# print(totals)

def create_category_aggregates(csv_path):
     """
     Computes a set of aggregates for each column.

     For numeric columns, computes:
       - Count, Missing Count, Sum, Mean, Median, Std, Variance, Min,
         25th, 50th, 75th percentiles, and Max.

     For categorical columns, computes:
       - Count, Missing Count, Unique Count, Mode,
         Top 3 most frequent values and their frequencies,
         Lowest 3 least frequent values and their frequencies.
     """
     df = pd.read_csv(csv_path)
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
     return numeric_df, categorical_df.T

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

def compare_columns(csv_path: str, column1: str, column2: str) -> str:
    """
    Compares two columns in the dataset by performing a cross-tabulation.
    Returns the result as a formatted string.
    """
    df = pd.read_csv(csv_path)
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

def sanitize_filename(name: str) -> str:
    """
    Replace characters that are not alphanumeric or underscores with an underscore.
    """
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)

def plot_smoothed_line_chart(csv_path: str, column1: str, column2: str, save_plot: bool = False, output_dir: str = "plots", max_points: int = 100):
    """
    Generates a simplified line chart comparing two numeric metrics from a CSV file,
    using a rolling average to smooth the data when there are many points.

    The function:
      - Reads and normalizes the CSV columns.
      - Uses fuzzy matching (via find_column) to resolve column names.
      - Checks that both columns are numeric.
      - Drops missing values and sorts the data by the first metric.
      - If the dataset has more points than max_points, computes a rolling average
        with a window size computed from the total number of points divided by max_points.
      - Plots the (smoothed) line chart with column1 on the x-axis and column2 on the y-axis.

    If save_plot is True, the chart is saved to output_dir (created if needed)
    and the file path is returned; otherwise, the chart is displayed.
    """
    df = pd.read_csv(csv_path)
    # Normalize column names: lower-case and strip whitespace.
    df.columns = df.columns.str.strip().str.lower()

    # Resolve actual column names using your fuzzy matching helper.
    col1 = find_column(df.columns, column1.strip().lower())
    col2 = find_column(df.columns, column2.strip().lower())

    if not col1 or not col2:
        error_msg = f"Error: Could not find column(s) '{column1}' or '{column2}'. Available columns: {df.columns.tolist()}"
        print(error_msg)
        return error_msg

    # Check that both columns are numeric.
    if not pd.api.types.is_numeric_dtype(df[col1]) or not pd.api.types.is_numeric_dtype(df[col2]):
        error_msg = "Error: Both columns must be numeric for a line chart comparison."
        print(error_msg)
        return error_msg

    # Drop missing values and sort by the first column.
    df = df[[col1, col2]].dropna().sort_values(by=col1)

    # Determine rolling window size based on data density.
    n_points = len(df)
    if n_points > max_points:
        window = max(1, int(n_points / max_points))
        df_smoothed = df.copy()
        df_smoothed[col1] = df_smoothed[col1].rolling(window=window, min_periods=1).mean()
        df_smoothed[col2] = df_smoothed[col2].rolling(window=window, min_periods=1).mean()
        x_data = df_smoothed[col1]
        y_data = df_smoothed[col2]
    else:
        x_data = df[col1]
        y_data = df[col2]

    plt.figure(figsize=(8, 6))
    plt.plot(x_data, y_data, marker='o', linestyle='-', color="blue")
    plt.xlabel(col1)
    plt.ylabel(col2)
    plt.title(f"Smoothed Line Chart: {col1} vs {col2}")
    plt.grid(True)
    
    if save_plot:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        safe_name = sanitize_filename(f"{col1}_vs_{col2}")
        file_path = os.path.join(output_dir, f"{safe_name}_smoothed_line_chart.png")
        plt.savefig(file_path, bbox_inches="tight", dpi=300)
        plt.close()
        print(f"Plot saved to: {file_path}")
        return file_path
    else:
        plt.show()
        return "Plot displayed."

async def stream_openai_response(response_iterator):
    """
    Simple streaming helper that yields OpenAI response chunks.
    """
    for chunk in response_iterator:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


