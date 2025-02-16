import os
import glob
import orjson
import logging
import threading
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Mistral + prompt imports
from mistralai import Mistral
from back.models.llm_outputs import RisksResponse
from back.prompts.prompt_diabetes import SYSTEM_DIABETES, PROMPT_DIABETES
from back.prompts.prompt_summary import SYSTEM_SUMMARY, PROMPT_SUMMARY
from back.helpers import load_patient_data, get_all_csv_files, create_chat_messages, get_chat_response

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

api_mistral = os.getenv("MISTRAL_API")
model = "mistral-large-latest"
client = Mistral(api_key=api_mistral)

# The order in which you want to analyze patients
PATIENT_ORDER = [
    "data/patient_0",
    "data/patient_1",
    "data/patient_2",
    "data/patient_3"
]

ANALYSIS_FOLDER = "analysis_results"

def analyze_patient_directory(patient_directory: str) -> dict:
    """
    Runs AI analysis for a single patient folder, returns the final JSON result.
    """
    patient_data_files = get_all_csv_files(patient_directory)
    all_data = []

    for data_path in patient_data_files:
        df_json = load_patient_data(data_path)
        all_data.append(df_json)

    data_messages = create_chat_messages(all_data, SYSTEM_DIABETES, PROMPT_DIABETES)
    logging.info(f"Analyzing patient data for {patient_directory}...")

    data_response = get_chat_response(
        client=client,
        model=model,
        messages=data_messages,
        response_format=RisksResponse
    )
    data_result_str = data_response.choices[0].message.content
    data_response_json = orjson.loads(data_result_str)
    data_response_json["sources"] = patient_data_files

    # Extract advices properly
    doctor_advices = [risk["doctor_advise"] for risk in data_response_json["risks"] if risk.get("doctor_advise")]
    patient_advices = [risk["patient_advise"] for risk in data_response_json["risks"] if risk.get("patient_advise")]

    logging.info("Preparing recommendations for doctors...")
    if doctor_advices:
        doc_sum_msgs = create_chat_messages(doctor_advices, SYSTEM_SUMMARY, PROMPT_SUMMARY)
        doc_sum_resp = get_chat_response(client, model, doc_sum_msgs, response_format="text")
        doctor_summary_str = doc_sum_resp.choices[0].message.content
    else:
        doctor_summary_str = "No doctor advice available."

    logging.info("Preparing recommendations for patients...")
    if patient_advices:
        pat_sum_msgs = create_chat_messages(patient_advices, SYSTEM_SUMMARY, PROMPT_SUMMARY)
        pat_sum_resp = get_chat_response(client, model, pat_sum_msgs, response_format="text")
        patient_summary_str = pat_sum_resp.choices[0].message.content
    else:
        patient_summary_str = "No patient advice available."

    final_output = {
        "initial_response": data_response_json,
        "doctor_summary": doctor_summary_str,
        "patient_summary": patient_summary_str
    }

    # Log the final result in pretty JSON
    logging.info("Analysis result for %s:\n%s", patient_directory,
                 orjson.dumps(final_output, option=orjson.OPT_INDENT_2).decode())
    return final_output

def background_precompute_in_order():
    """
    Background thread: analyze each patient in PATIENT_ORDER sequentially,
    writing each result to a JSON file as soon as it's done.
    """
    if not os.path.exists(ANALYSIS_FOLDER):
        os.makedirs(ANALYSIS_FOLDER)

    for pdir in PATIENT_ORDER:
        logging.info(f"[Background] Precomputing analysis for {pdir}...")
        try:
            result = analyze_patient_directory(pdir)
            folder_name = os.path.basename(pdir)  # e.g. "patient_0"
            out_path = os.path.join(ANALYSIS_FOLDER, f"{folder_name}.json")
            # Write multiline JSON
            with open(out_path, "wb") as f:
                f.write(orjson.dumps(result, option=orjson.OPT_INDENT_2))
            logging.info(f"[Background] Wrote analysis to {out_path}")
        except Exception as e:
            logging.error(f"[Background] Error analyzing {pdir}: {e}")

# ----------------- FastAPI Setup -----------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """
    On server startup, spawn a background thread to do the analysis in order.
    The first patient_0 result will appear as soon as that analysis finishes,
    while the rest continue analyzing.
    """
    logging.info("Spawning background thread for analysis in order...")
    t = threading.Thread(target=background_precompute_in_order, daemon=True)
    t.start()
    logging.info("Background thread started. We can now serve partial results once each file is ready.")

@app.get("/analysis/{patient_id}")
def get_analysis_json(patient_id: str):
    """
    Returns the precomputed JSON for patient_id (e.g. 'patient_0').
    If the file isn't created yet, we return 404 so the front end can handle it.
    """
    path = os.path.join(ANALYSIS_FOLDER, f"{patient_id}.json")
    if not os.path.exists(path):
        logging.error(f"No JSON file found for {patient_id} at {path} (maybe still analyzing?)")
        raise HTTPException(status_code=404, detail=f"No analysis found yet for {patient_id}")
    with open(path, "rb") as f:
        data = orjson.loads(f.read())
    return data

@app.get("/")
def root():
    return {"message": "Welcome to the partial results backend! Some analyses may still be in progress."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("back.main:app", host="127.0.0.1", port=8000, reload=True)
