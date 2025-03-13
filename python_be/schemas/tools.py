tools = [
    {
        "type": "function",
        "function": {
            "name": "get_min_max_mean",
            "description": "Get the minimum maximum and average values per column",
            "parameters": {
                "type": "object",
                "properties": {
                    "csv_path": {
                        "type": "string",
                        "description": "Path to the CSV file"
                    }
                },
                "required": ["csv_path"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_category_aggregates",
            "description": "Computes a set of aggregates for each column. Has both numeric and categorical columns and gives insights on frequency of appearence of each column",
            "parameters": {
                "type": "object",
                "properties": {
                    "csv_path": {
                        "type": "string",
                        "description": "Path to the CSV file"
                    },
                     "column_of_interest": {
                        "type": "string",
                        "description": "Name of the column to focus on for charting"
                    }
                },
                "required": ["csv_path"]
            },
        }
    },
        {
        "type": "function",
        "function": {
            "name": "compare_columns",
            "description": "Compares any two columns in a CSV file by performing a cross-tabulation and returning aggregated data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "csv_path": {
                        "type": "string",
                        "description": "Path to the CSV file"
                    },
                    "column1": {
                        "type": "string",
                        "description": "Name of the first column to compare"
                    },
                    "column2": {
                        "type": "string",
                        "description": "Name of the second column to compare"
                    }
                },
                "required": ["csv_path", "column1", "column2"]
            },
        }
    }
]