from mistralai import Mistral
from dotenv import load_dotenv
import os
import glob
import orjson
import logging
import pandas as pd
from pydantic import BaseModel
from typing import List

# Import helper modules and prompts
from back.models.llm_outputs import *  
from back.prompts.prompt_diabetes import SYSTEM_DIABETES, PROMPT_DIABETES
from back.prompts.prompt_summary import SYSTEM_SUMMARY, PROMPT_SUMMARY
from back.helpers import load_patient_data, get_all_csv_files, create_chat_messages, get_chat_response

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

api_mistral = os.getenv("MISTRAL_API")
model = "mistral-large-latest"

client = Mistral(api_key=api_mistral)

def general_llm_call(patient_directory: str):
    patient_data_files = get_all_csv_files(patient_directory)
    all_data = []
    for data_path in patient_data_files:
        df_json = load_patient_data(data_path)
        all_data.append(df_json)
    data_messages = create_chat_messages(all_data, SYSTEM_DIABETES, PROMPT_DIABETES)
    logging.info("Analyzing patient data...")
    data_response = get_chat_response(
        client=client,
        model=model,
        messages=data_messages,
        response_format=RisksResponse
    )
    data_result = data_response.choices[0].message.content
    data_response = orjson.loads(data_result)
    data_response["sources"] = patient_data_files
    doctor_advices = [risk["doctor_advise"] for risk in data_response["risks"] if risk["doctor_advise"]]
    patient_advices = [risk["patient_advise"] for risk in data_response["risks"] if risk["patient_advise"]]
    logging.info("Preparing recommendations for doctors...")
    doctor_summary_messages = create_chat_messages(doctor_advices, SYSTEM_SUMMARY, PROMPT_SUMMARY) if doctor_advices else "No doctor advice available."
    doctor_summary_result = get_chat_response(
        client=client,
        model=model,
        messages=doctor_summary_messages,
        response_format="text"
    )
    doctor_summary_response = doctor_summary_result.choices[0].message.content
    logging.info("Preparing recommendations for patients...")
    patient_summary_messages = create_chat_messages(patient_advices, SYSTEM_SUMMARY, PROMPT_SUMMARY) if patient_advices else "No patient advice available."
    patient_summary_result = get_chat_response(
        client=client,
        model=model,
        messages=patient_summary_messages,
        response_format="text"
    )
    patient_summary_response = patient_summary_result.choices[0].message.content
    final_output = {
        "initial_response": data_response,
        "doctor_summary": doctor_summary_response,
        "patient_summary": patient_summary_response
    }
    logging.info(orjson.dumps(final_output, option=orjson.OPT_INDENT_2).decode())
    return final_output

# FastAPI Server Setup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
class AnalyzeRequest(BaseModel):
    directory: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
def analyze_patient(data: AnalyzeRequest):
    try:
        result = general_llm_call(data.directory)
        return result
    except Exception as e:
        logging.error(f"Error analyzing patient data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("back.mistral_diabetes:app", host="127.0.0.1", port=8000, reload=True)
