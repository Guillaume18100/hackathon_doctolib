SYSTEM_DIABETES = "You are a medical AI assistant specialized in calculating the risk of Type 2 diabetes using the provided patient information."

PROMPT_DIABETES = """### Instructions
    
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

    Output analysis only for components listed above, your analysis should only focus on diabetes, do not include other issues.

    ### Potential Primary Risks:"""