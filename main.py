import json
from openai import OpenAI
from pydantic import BaseModel, Field
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS middleware to allow requests from your front end.
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000"
    # Add any other origins you might use
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Relax this for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set your preferred model and API key
MODEL = "deepseek-r1"  # Adjust if needed
API_KEY = "57033301-8c34-4cae-b78b-fc025a54fda7"  # Replace with your actual Scaleway API key

client = OpenAI(
    base_url="https://api.scaleway.ai/v1",
    api_key=API_KEY,
)

class ChatPayload(BaseModel):
    message: str

@app.post("/chat")
def chat_endpoint(payload: ChatPayload):
    transcript = payload.message
    if not transcript:
        return {"error": "No transcript provided"}

    response = get_pathology_response(transcript)
    return response

# Define a Pydantic schema tailored for pathology responses
class PathologyResponse(BaseModel):
    caseSummary: str = Field(..., description="A concise summary of the pathology case details")
    differentialDiagnosis: list[str] = Field(..., description="List of possible diagnoses")
    recommendedTests: list[str] = Field(..., description="List of additional tests recommended")
    additionalNotes: str = Field(..., description="Additional clinical notes or recommendations")

def get_pathology_response(transcript: str) -> dict:
    extract = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI assistant specialized in pathology. The following is a pathology report transcript. "
                    "Please provide a structured JSON response with the fields: caseSummary, differentialDiagnosis, "
                    "recommendedTests, and additionalNotes. Answer only in JSON."
                ),
            },
            {
                "role": "user",
                "content": transcript,
            },
        ],
        model=MODEL,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "PathologyResponse",
                "schema": PathologyResponse.model_json_schema(),
            }
        },
    )
    output = json.loads(extract.choices[0].message.content)
    return output

if __name__ == "__main__":
    print("=== Pathology Chatbot ===")
    print("Enter a pathology report transcript below (type 'exit' to quit):\n")
    while True:
        transcript = input("Transcript: ")
        if transcript.lower().strip() == "exit":
            break
        try:
            response = get_pathology_response(transcript)
            print("\nAI Response:")
            print(json.dumps(response, indent=2))
        except Exception as e:
            print("An error occurred:", e)
        print("\n--------------------------------\n")