
import os
import base64
from openai import AzureOpenAI

endpoint = os.getenv("ENDPOINT_URL", "https://cmd4.openai.azure.com/openai/deployments/o3/chat/completions?api-version=2025-01-01-preview")
deployment = os.getenv("DEPLOYMENT_NAME", "o3")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY", "XXX")

# Initialize Azure OpenAI client with key-based authentication
client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version="2025-01-01-preview",
)

IMAGE_PATH = r"d:\data\HCNC\norway\biographies\raw\corpus\digibok_2007031501007\digibok_2007031501007_0103.jpg"
encoded_image = base64.b64encode(open(IMAGE_PATH, 'rb').read()).decode('utf-8')

#Prepare the chat prompt
chat_prompt = [
    {
        "role": "developer",
        "content": [
            {
                "type": "text",
                "text": "You are an AI assistant that helps people find information."
            }
        ]
    },
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "\n"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{encoded_image}"
                }
            },
            {
                "type": "text",
                "text": "Please transcribe this norwegian biography. Respond in markdown. Please tag the embedded portraits exactly as they appear in the text. Please note that there might be two columns of text. Make sure to transcribe the text in the correct order, first columns 1 from top to bottom and then column 2 from top to buttom. Please reason step by step and provide the final result in a single markdown code block. Do not include any additional text or explanations outside the code block. Make sure not to read from column 2 before you have read all of column 1. If you encounter any issues with the image, please let me know."
            }
        ]
    }
]

# Include speech result if speech is enabled
messages = chat_prompt

# Generate the completion
completion = client.chat.completions.create(
    model=deployment,
    messages=messages,
    max_completion_tokens=10000,
    stop=None,
    stream=False,
    reasoning_effort="medium",
    temperature=0.1,
)

print(completion.to_json())
    