from mistralai import Mistral
from dotenv import load_dotenv
import os
import glob
import orjson
import logging
import pandas as pd
from pydantic import BaseModel
from typing import List

load_dotenv()
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

api_mistral = os.getenv("MISTRAL_API")

# Specify model
model = "mistral-large-latest"

# Output structure
class Risk(BaseModel):
    risk: str
    severity_level: str
    therapeutic_goal: str
    doctor_advise: str
    patient_advise: str
    observations: str

class RisksResponse(BaseModel):
    risks: List[Risk]

# Initialize the Mistral client
client = Mistral(api_key=api_mistral)

def load_patient_data(file_path: str) -> str:
    """Loads patient data from a CSV file and converts it to JSON format."""
    data = pd.read_csv(file_path)
    return data.to_json(orient="records")

def get_all_csv_files(directory: str) -> list:
    """Recursively finds all CSV files in the given directory."""
    return glob.glob(os.path.join(directory, "**", "*.csv"), recursive=True)

def create_chat_messages(patient_data: list) -> list:
    """Creates chat messages with system instructions and patient data."""
    return [
        {
            "role": "system",
            "content": "You are a medical AI assistant specialized in calculating the risk of Type 2 diabetes using the provided patient information."
        },
        {
            "role": "user",
            "content": f"""### Instructions
    
    I will provide you with observations data for one patient. Please follow the methodology provided below and output the diabetes risk probability (0-100%). Provide a brief explanation of each component and severity level. Set a theraputic goal for the patient to reduce a given risk. Provide both patient and doctor with advise to reduce the risk. The advise should contain exact actions to perform enriched with numbers of potential improvement of a given component (like "A balanced diet could reduce cholesterol level by 40%").

    Be as specific as possible in terms of advise: 
        - for the doctor: a concrete action for the patient in terms of lifestyle
        - for the patient: a concrete medication to prescribe for a psecific purpose, a concrete analysis to perform for a psecific purpose.
    
    If the patient data is missing on some component, mark `severity_level` as Unknown, alert the healcare professional about the necessity to fill in the missing info through 
        - analisys presciption
        - treatement prescription
        - questionnaire for lifestyle to fill in. 

    ###Methodology by component

    1. Age:

        - Risk increases with age. For each decade over 45 years, risk increases by approximately 5-10%.
    
    2. Family History:

        - If the patient has a first-degree relative with diabetes, increase risk by 5-10%.
    
    3. Body Mass Index (BMI):

        - BMI ≥ 25 kg/m²: Increased risk (higher the BMI, the higher the risk).
        - Each 1 kg/m² increase in BMI increases risk by 1-3%.
    
    4. Blood Pressure:

        - Systolic BP ≥ 130 mmHg or Diastolic BP ≥ 85 mmHg: Increased risk. A 10 mmHg increase in BP can increase risk by about 2-5%.
    
    5. Fasting Glucose:

        - Fasting glucose ≥ 100 mg/dL: Risk increases substantially. A value between 100-125 mg/dL suggests prediabetes, with a 20-30% risk of developing diabetes within 5 years.
        - Fasting glucose ≥ 126 mg/dL: Strong indicator of diabetes risk.
    
    6. HbA1c Levels:

        - HbA1c ≥ 5.7%: Increases the risk. Between 5.7%-6.4% is considered prediabetes, with a higher risk of progression to Type 2 diabetes.
    
    7. Cholesterol Levels (HDL, LDL, Triglycerides):

        - Low HDL (< 40 mg/dL for men, < 50 mg/dL for women): Increased risk.
        - High Triglycerides (> 150 mg/dL) and LDL > 130 mg/dL: Also contribute to risk.
    
    8. Lifestyle Factors:

        - Physical Activity: Sedentary individuals have significantly higher risk. Increased risk for those with minimal or no regular physical activity.
        - Diet: High sugar, high fat, and low fiber intake increases risk. A poor diet can increase risk by 5-15%.
        - Smoking: Smokers have an increased risk (by 10-20%).
        - Alcohol: High alcohol intake can also contribute to risk.

    9. Sleep and Stress:

        - Poor sleep (< 6 hours per night) and high stress levels contribute to higher risk due to metabolic dysfunction, with an increase of up to 10%.

    ### Patient data:

    {patient_data}

    ### Potential Primary Risks:"""
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


def summarize_list(items: list, summary_type: str) -> str:
    """Calls the LLM to summarize a list of advices."""
    summary_messages = [
        {"role": "system", "content": f"You are an AI specialized in summarizing {summary_type}."},
        {"role": "user", "content": f"Summarize the following {summary_type} list in a concise wa, with no introduction:\n\n" + "\n".join(items)}
    ]

    summary_response = get_chat_response(
        client=client,
        model=model,
        messages=summary_messages,
        response_format="text"
    )

    return summary_response.choices[0].message.content

def general_llm_call(patient_directory: str):
    """General function to execute the workflow."""
    patient_data_files = get_all_csv_files(patient_directory)
    all_data = []

    for data_path in patient_data_files:
        df_json = load_patient_data(data_path)
        all_data.append(df_json)

    messages = create_chat_messages(all_data)

    logging.info("Analyzing patient data...")
    chat_response = get_chat_response(
        client=client,
        model=model,
        messages=messages,
        response_format=RisksResponse
    )

    # Extract initial results
    result = chat_response.choices[0].message.content
    result = orjson.loads(result)
    result["sources"] = patient_data_files

    # Extract doctor and patient advice lists
    doctor_advices = [risk["doctor_advise"] for risk in result["risks"] if risk["doctor_advise"]]
    patient_advices = [risk["patient_advise"] for risk in result["risks"] if risk["patient_advise"]]

    # Summarize doctor and patient advice
    logging.info("Preparing recommendations for doctors...")
    doctor_summary = summarize_list(doctor_advices, "doctor advice") if doctor_advices else "No doctor advice available."
    logging.info("Preparing recommendations for patients...")
    patient_summary = summarize_list(patient_advices, "patient advice") if patient_advices else "No patient advice available."

    # Final output
    final_output = {
        "initial_response": result,
        "doctor_summary": doctor_summary,
        "patient_summary": patient_summary
    }

    logging.info(orjson.dumps(final_output, option=orjson.OPT_INDENT_2).decode())

if __name__ == "__main__":
    patient_data = "data/patient_1"
    general_llm_call(patient_data)
