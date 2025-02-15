import os
import logging
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Import your real Mistral logic from test_mistral.py
# e.g. from test_mistral import general_llm_call
# Or if you prefer, just copy-paste the code from test_mistral.py directly here.

# ------------------------------------------------------------------
# Directly copy the relevant code from test_mistral.py for clarity:
# ------------------------------------------------------------------
from mistralai import Mistral
import glob
import orjson

api_mistral = os.getenv("MISTRAL_API")
model = "mistral-large-latest"

client = Mistral(api_key=api_mistral)

def load_patient_data(file_path: str) -> str:
    data = pd.read_csv(file_path)
    return data.to_json(orient="records")

def get_all_csv_files(directory: str) -> list:
    return glob.glob(os.path.join(directory, "**", "*.csv"), recursive=True)

def create_chat_messages(patient_data: list) -> list:
    return [
        {
            "role": "system",
            "content": "You are a medical AI assistant specialized in calculating the risk of Type 2 diabetes using the provided patient information."
        },
        {
            "role": "user",
            "content": f"""### Instructions
I will provide you with observations data for one patient. Please follow the methodology...
[the rest of your instructions here...]
### Patient data:
{patient_data}
### Potential Primary Risks:"""
        },
    ]

class Risk(BaseModel):
    risk: str
    severity_level: str
    therapeutic_goal: str
    doctor_advise: str
    patient_advise: str
    observations: str

class RisksResponse(BaseModel):
    risks: List[Risk]

def get_chat_response(client, model, messages, response_format, max_tokens=4096, temperature=0.0):
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

def summarize_list(items: list, summary_type: str) -> str:
    summary_messages = [
        {"role": "system", "content": f"You are an AI specialized in summarizing {summary_type}."},
        {"role": "user", "content": f"Summarize the following {summary_type} list in a concise way, with no introduction:\n\n" + "\n".join(items)}
    ]

    summary_response = get_chat_response(
        client=client,
        model=model,
        messages=summary_messages,
        response_format="text"
    )
    return summary_response.choices[0].message.content

def general_llm_call(patient_directory: str):
    """Real function that calls Mistral with CSV data for the given directory."""
    patient_data_files = get_all_csv_files(patient_directory)
    all_data = []

    for data_path in patient_data_files:
        df_json = load_patient_data(data_path)
        all_data.append(df_json)

    messages = create_chat_messages(all_data)
    logging.info("Analyzing patient data with Mistral...")

    chat_response = get_chat_response(
        client=client,
        model=model,
        messages=messages,
        response_format=RisksResponse
    )

    # Convert to Python object
    result = chat_response.choices[0].message.content
    result = orjson.loads(result)

    # Add the file paths as "sources"
    result["sources"] = patient_data_files

    # Summaries
    doctor_advices = [risk["doctor_advise"] for risk in result["risks"] if risk["doctor_advise"]]
    patient_advices = [risk["patient_advise"] for risk in result["risks"] if risk["patient_advise"]]

    doctor_summary = summarize_list(doctor_advices, "doctor advice") if doctor_advices else "No doctor advice available."
    patient_summary = summarize_list(patient_advices, "patient advice") if patient_advices else "No patient advice available."

    final_output = {
        "initial_response": result,
        "doctor_summary": doctor_summary,
        "patient_summary": patient_summary
    }
    logging.info(orjson.dumps(final_output, option=orjson.OPT_INDENT_2).decode())
    return final_output
# ------------------------------------------------------------------

# Now we set up FastAPI
app = FastAPI()

class AnalyzeRequest(BaseModel):
    directory: str

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
def analyze_patient(data: AnalyzeRequest):
    """
    The front-end will call POST /analyze with { "directory": "data/patient_X" }.
    We'll pass that directory to the real general_llm_call above.
    """
    try:
        result = general_llm_call(data.directory)
        return result
    except Exception as e:
        logging.error(f"Error analyzing patient data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Welcome to PathAI backend with real Mistral logic!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
