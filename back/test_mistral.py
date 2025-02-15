from mistralai import Mistral
from dotenv import load_dotenv
import os
import pandas as pd
from pydantic import BaseModel
from typing import List

load_dotenv()

api_mistral = os.getenv("MISTRAL_API")

# Specify model
model = "mistral-large-latest"

# Output structure
class Risk(BaseModel):
    risk: str
    severity_level: str
    advise: str
    observations: str

class RisksResponse(BaseModel):
    risks: List[Risk]

# Initialize the Mistral client
client = Mistral(api_key=api_mistral)

def load_patient_data(file_path: str) -> str:
    """Loads patient data from a CSV file and converts it to JSON format."""
    data = pd.read_csv(file_path)
    return data.to_json(orient="records")

def create_chat_messages(patient_data_json: str) -> list:
    """Creates chat messages with system instructions and patient data."""
    return [
        {
            "role": "system",
            "content": "You are a medical AI assistant specialized with calculating the risk of Type 2 diabetes using the following patient information."
        },
        {
            "role": "user",
            "content": f"""### Instructions
    
    I will provide you with observations data for one patient. Please follow the methodology provided below and output the diabetes risk probability (0-100%). Provide a brief explanation of each component, severity level and advise to reduce the risk. If the patient data is missing on some component, mark `severity_level` as Unknown, alert the healcare professional about the necessity to fill in the missing info, through analisys performance or questionnaire.

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

    Medical observations: 
    {patient_data_json}
    
    ### Potential primary risks:"""
        },
    ]

def get_chat_response(client, model, messages, response_format, max_tokens=2048, temperature=0.0):
    """Sends a chat request and retrieves the response."""
    return client.chat.parse(
        model=model,
        messages=messages,
        response_format=response_format,
        max_tokens=max_tokens,
        temperature=temperature
    )

def main(file_path):
    """Main function to execute the workflow."""
    patient_data_json = load_patient_data(file_path)
    messages = create_chat_messages(patient_data_json)

    chat_response = get_chat_response(
        client=client,
        model=model,
        messages=messages,
        response_format=RisksResponse
    )

    print(chat_response.choices[0].message.content)

if __name__ == "__main__":
    main("data/observations/patient_1.csv")
