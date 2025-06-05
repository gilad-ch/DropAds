import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables.")

client = OpenAI(api_key=api_key)

def _encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def prompt_image(system_prompt: str, user_prompt: str, image_path: str) -> str:
    base64_image = _encode_image(image_path)

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    },
                ],
            },
        ],
        max_tokens=300
    )

    return response.choices[0].message.content.strip()

# Main function to generate a response from a prompt
def prompt_llm(prompt: str, system_message: str = None) -> str:
    if not system_message:
        system_message = (
            "Only reply with the asked description text and nothing else!"
        )

    response = client.chat.completions.create(
        model="gpt-4o",  # or "gpt-4-turbo" if preferred
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300
    )

    return response.choices[0].message.content.strip()

