import os
import logging
from openai import OpenAI
from utils.get_parameters import get_ssm_parameter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL = "gpt-4o-mini"

def get_openai_api_key() -> str:
    """Retrieve OpenAI API Key from environment variables or AWS SSM Parameter Store."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.warning("OpenAI API Key not set.")
    else:
        logger.info(f"OpenAI API Key loaded successfully (Starts with: {api_key[:8]})")
    
    return api_key

def chat(message: str, history: list=[], system_message: str = "You are a helpful assistant.") -> tuple:
    """
    Sends a chat message to OpenAI and returns the response with updated conversation history.

    Args:
        message (str): User's message.
        history (list): List of previous messages (conversation history).
        system_message (str): System-level instructions for the model.

    Returns:
        tuple: Response message (str) and updated history (list).
    """
    api_key = get_openai_api_key()
    if not api_key:
        return "Error: OpenAI API Key is missing.", history  # Return error message

    openai = OpenAI()

    # Prepare conversation messages
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]

    try:
        # Stream response from OpenAI
        stream = openai.chat.completions.create(model=MODEL, messages=messages, stream=True)

        # Efficiently accumulate response text
        response = "".join(chunk.choices[0].delta.content or "" for chunk in stream)

        # Update history
        updated_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response}
        ]

        return response, updated_history

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return f"Error: {str(e)}", history
