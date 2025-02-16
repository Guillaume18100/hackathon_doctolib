# Not implemented in current context

import warnings
import os
from typing import *
from dotenv import load_dotenv
from transformers import logging
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
# from interface import create_demo #Commented out as not used in batch mode
from medrax.agent import *
from medrax.tools import *
from medrax.utils import *
import glob  # Import the glob module
import time
from pathlib import Path
import json  # For writing json output
import re

warnings.filterwarnings("ignore")
logging.set_verbosity_error()
load_dotenv()

api_openai = os.getenv("OPENAI_API")
if api_openai is None:
    raise ValueError("Missing OpenAI API Key. Please set it in the .env file.")

def clean_markdown_json(text: str) -> str:
    """
    Remove markdown formatting (e.g., triple backticks) from the text if present.
    """
    text = text.strip()
    # Remove leading and trailing triple backticks and any language specifier (like "json")
    if text.startswith("```"):
        # Remove the starting triple backticks and optional language tag
        text = re.sub(r"^```(?:json)?\s*", "", text)
        # Remove trailing triple backticks
        text = re.sub(r"\s*```$", "", text)
    return text

def initialize_agent(
    prompt_file, tools_to_use=None, model_dir="/model-weights", temp_dir="temp", device="cuda"
):
    """Initialize the MedRAX agent with specified tools and configuration."""
    prompts = load_prompts_from_file(prompt_file)
    prompt = prompts["MEDICAL_ASSISTANT"]
    all_tools = {
        "ChestXRayClassifierTool": lambda: ChestXRayClassifierTool(device=device)
    }
    tools_dict = {}
    tools_to_use = tools_to_use or all_tools.keys()
    for tool_name in tools_to_use:
        if tool_name in all_tools:
            tools_dict[tool_name] = all_tools[tool_name]()
    checkpointer = MemorySaver()
    model = ChatOpenAI(model="gpt-4o", temperature=0.7, top_p=0.95, api_key=api_openai)
    agent = Agent(
        model,
        tools=list(tools_dict.values()),
        log_tools=True,
        log_dir="logs",
        system_prompt=prompt,
        checkpointer=checkpointer,
    )
    print("Agent initialized")
    return agent, tools_dict

def process_image_and_prompt(agent, image_path, prompt):
    """
    Process a single image with the given prompt using the agent's workflow.
    Instead of printing, this function writes the final agent response as a JSON object
    to a file named TEST.json in the same folder as the image.
    
    Args:
        agent: The initialized MedRAX agent.
        image_path (str): Path to the image file.
        prompt (str): The text prompt to use.
    """
    final_output = None  # This will hold our final JSON result

    messages = []
    messages.append({"role": "user", "content": f"path: {image_path}"})
    messages.append({"role": "user", "content": prompt})

    try:
        # Iterate over the streaming events from the agent.
        for event in agent.workflow.stream(
            {"messages": messages},
            {"configurable": {"thread_id": str(time.time())}}
        ):
            # We only care about the agent's textual (process) response.
            if isinstance(event, dict) and "process" in event:
                content = event["process"]["messages"][-1].content
                if content:
                    cleaned_content = clean_markdown_json(content)
                    try:
                        # Try to parse the cleaned content as JSON.
                        parsed = json.loads(cleaned_content)
                        final_output = parsed  # Update final_output with the parsed dictionary.
                    except Exception as parse_error:
                        print(f"Could not parse agent response as JSON: {parse_error}")
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")

    # Determine the patient folder and create the output file path.
    patient_folder = os.path.dirname(image_path)
    output_file = os.path.join(patient_folder, "TEST.json")
    
    if final_output is None:
        print("No valid JSON response found; nothing to write.")
    else:
        # Write the final output JSON object to TEST.json
        with open(output_file, "w") as f:
            json.dump(final_output, f, indent=2)
        print(f"Output written to {output_file}")

def main():
    """
    Main function to initialize the agent and process images from patient folders.
    """
    print("Starting batch processing...")
    selected_tools = ["ChestXRayClassifierTool"]
    agent, tools_dict = initialize_agent(
        "medrax/docs/system_prompts.txt", tools_to_use=selected_tools, model_dir="/model-weights"
    )

    # Specify the base data directory - use the absolute path provided
    base_data_dir = "/root/users/hackathon_doctolib/data"
    # Create the full path to the patient folders
    patient_folders = sorted(glob.glob(os.path.join(base_data_dir, "patient_*")))

    if not patient_folders:
        print(f"No patient folders found in '{base_data_dir}'. Ensure the directory exists and contains patient folders (patient_0, patient_1, ...).")
        return

    prompt = "Only return: cardiomegaly, effusion, edema, enlarged cardiomediastinum results as a json file."

    for patient_folder in patient_folders:
        image_path = os.path.join(patient_folder, "xray.jpg")
        if os.path.exists(image_path):
            print(f"Processing image: {image_path}")
            process_image_and_prompt(agent, image_path, prompt)
        else:
            print(f"Image not found in {patient_folder}")

if __name__ == "__main__":
    main()