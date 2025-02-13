import re
from openai import OpenAI
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

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

def remove_chain_of_thought(text: str) -> str:
    """
    Removes any text between <think> and </think> tags, including the tags themselves.
    """
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

# Endpoint now returns plain text.
@app.post("/chat", response_class=PlainTextResponse)
def chat_endpoint(payload: ChatPayload):
    transcript = payload.message
    if not transcript:
        return "Error: No transcript provided."
    
    response_text = get_pathology_response(transcript)
    filtered_text = remove_chain_of_thought(response_text)
    return filtered_text

def get_pathology_response(transcript: str) -> str:
    """
    Sends the pathology transcript to the AI and returns a structured plain text response.
    The system message instructs the AI to output only the final structured plain text response,
    ignoring any chain-of-thought or internal reasoning (including text between <think> tags).
    """
    result = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI assistant specialized in pathology. The following is a pathology report transcript.\n\n"
                    "Please provide a structured, easy-to-read plain text response with the following sections:\n\n"
                    "--------------------------------------------------\n"
                    "CASE SUMMARY\n"
                    "--------------------------------------------------\n"
                    "DIFFERENTIAL DIAGNOSIS (list each diagnosis as a bullet point using '-' for bullets)\n"
                    "--------------------------------------------------\n"
                    "RECOMMENDED TESTS (list each test as a bullet point using '-' for bullets)\n"
                    "--------------------------------------------------\n"
                    "ADDITIONAL NOTES\n"
                    "--------------------------------------------------\n\n"
                    "Ensure each section is clearly separated and formatted for readability. "
                    "Do not use any markdown formatting symbols (such as asterisks or underscores). "
                    "Ignore any internal chain-of-thought or reasoning text, including anything enclosed in <think> tags. "
                    "Output only the final structured plain text response."
                ),
            },
            {
                "role": "user",
                "content": transcript,
            },
        ],
        model=MODEL,
    )
    return result.choices[0].message.content

if __name__ == "__main__":
    print("=== Pathology Chatbot ===")
    print("Enter a pathology report transcript below (type 'exit' to quit):\n")
    while True:
        transcript = input("Transcript: ")
        if transcript.lower().strip() == "exit":
            break
        try:
            response_text = get_pathology_response(transcript)
            filtered_text = remove_chain_of_thought(response_text)
            print("\nAI Response:\n")
            print(filtered_text)
        except Exception as e:
            print("An error occurred:", e)
        print("\n--------------------------------\n")