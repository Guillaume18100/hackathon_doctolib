import os
import glob
import pandas as pd

def load_patient_data(file_path: str) -> str:
    """Loads patient data from a CSV file and converts it to JSON format."""
    data = pd.read_csv(file_path)
    return data.to_json(orient="records")

def get_all_csv_files(directory: str) -> list:
    """Recursively finds all CSV files in the given directory."""
    return glob.glob(os.path.join(directory, "**", "*.csv"), recursive=True)

def create_chat_messages(data: list, system: str, prompt: str) -> list:
    """Creates chat messages with system instructions and patient data."""
    return [
        {
            "role": "system",
            "content": system
        },
        {
            "role": "user",
            "content": prompt.format(patient_data=data)
        },
    ]

def get_chat_response(client, model, messages, response_format, max_tokens=4096, temperature=0.0):
    """Sends a chat request and retrieves the response."""
    if response_format == "text":
        return client.chat.complete(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
    else:
        return client.chat.parse(
            model=model,
            messages=messages,
            response_format=response_format,
            max_tokens=max_tokens,
            temperature=temperature
        )
