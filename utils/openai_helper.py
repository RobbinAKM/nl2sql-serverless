import os
import logging
from openai import OpenAI
from utils.db_helper import get_schema_by_id
from utils.get_parameters import get_ssm_parameter
from utils.get_system_message import get_system_message

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL = "gpt-4o-mini"
# db_schema = {
#     "tables": [
#         "categories", "order_items", "orders", "payments", "products", "shipping", "users"
#     ],
#     "shipping": {
#         "foreign_keys": [
#             {"column": ["order_id"], "referenced_columns": ["id"], "referenced_table": "orders"},
#             {"column": ["user_id"], "referenced_columns": ["id"], "referenced_table": "users"}
#         ],
#         "primary_keys": ["id"],
#         "indexes": [
#             {"name": "order_id", "columns": ["order_id"], "unique": False},
#             {"name": "user_id", "columns": ["user_id"], "unique": False}
#         ],
#         "columns": [
#             {"name": "id", "type": "INTEGER"},
#             {"name": "order_id", "type": "INTEGER"},
#             {"name": "user_id", "type": "INTEGER"},
#             {"name": "shipping_address", "type": "VARCHAR(255)"},
#             {"name": "shipping_status", "type": "VARCHAR(50)"},
#             {"name": "estimated_delivery", "type": "DATETIME"}
#         ]
#     },
#     "payments": {
#         "foreign_keys": [
#             {"column": ["order_id"], "referenced_columns": ["id"], "referenced_table": "orders"},
#             {"column": ["user_id"], "referenced_columns": ["id"], "referenced_table": "users"}
#         ],
#         "primary_keys": ["id"],
#         "indexes": [
#             {"name": "order_id", "columns": ["order_id"], "unique": False},
#             {"name": "user_id", "columns": ["user_id"], "unique": False}
#         ],
#         "columns": [
#             {"name": "id", "type": "INTEGER"},
#             {"name": "order_id", "type": "INTEGER"},
#             {"name": "user_id", "type": "INTEGER"},
#             {"name": "amount", "type": "FLOAT"},
#             {"name": "payment_status", "type": "VARCHAR(50)"}
#         ]
#     },
#     "orders": {
#         "foreign_keys": [
#             {"column": ["user_id"], "referenced_columns": ["id"], "referenced_table": "users"}
#         ],
#         "primary_keys": ["id"],
#         "indexes": [{"name": "user_id", "columns": ["user_id"], "unique": False}],
#         "columns": [
#             {"name": "id", "type": "INTEGER"},
#             {"name": "user_id", "type": "INTEGER"},
#             {"name": "total_price", "type": "FLOAT"},
#             {"name": "order_status", "type": "VARCHAR(50)"}
#         ]
#     },
#     "categories": {
#         "foreign_keys": [],
#         "primary_keys": ["id"],
#         "indexes": [{"name": "name", "columns": ["name"], "unique": True}],
#         "columns": [
#             {"name": "id", "type": "INTEGER"},
#             {"name": "name", "type": "VARCHAR(50)"}
#         ]
#     },
#     "users": {
#         "foreign_keys": [],
#         "primary_keys": ["id"],
#         "indexes": [{"name": "email", "columns": ["email"], "unique": True}],
#         "columns": [
#             {"name": "id", "type": "INTEGER"},
#             {"name": "name", "type": "VARCHAR(100)"},
#             {"name": "email", "type": "VARCHAR(100)"},
#             {"name": "password", "type": "VARCHAR(100)"},
#             {"name": "address", "type": "VARCHAR(255)"}
#         ]
#     },
#     "order_items": {
#         "foreign_keys": [
#             {"column": ["order_id"], "referenced_columns": ["id"], "referenced_table": "orders"},
#             {"column": ["product_id"], "referenced_columns": ["id"], "referenced_table": "products"}
#         ],
#         "primary_keys": ["id"],
#         "indexes": [
#             {"name": "order_id", "columns": ["order_id"], "unique": False},
#             {"name": "product_id", "columns": ["product_id"], "unique": False}
#         ],
#         "columns": [
#             {"name": "id", "type": "INTEGER"},
#             {"name": "order_id", "type": "INTEGER"},
#             {"name": "product_id", "type": "INTEGER"},
#             {"name": "quantity", "type": "INTEGER"},
#             {"name": "price", "type": "FLOAT"}
#         ]
#     },
#     "products": {
#         "foreign_keys": [
#             {"column": ["category_id"], "referenced_columns": ["id"], "referenced_table": "categories"}
#         ],
#         "primary_keys": ["id"],
#         "indexes": [{"name": "category_id", "columns": ["category_id"], "unique": False}],
#         "columns": [
#             {"name": "id", "type": "INTEGER"},
#             {"name": "name", "type": "VARCHAR(100)"},
#             {"name": "description", "type": "VARCHAR(255)"},
#             {"name": "price", "type": "FLOAT"},
#             {"name": "stock", "type": "INTEGER"},
#             {"name": "category_id", "type": "INTEGER"}
#         ]
#     }
# }


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
        return "Error: OpenAI API Key is missing."  # Return error message

    # Fetch schema from DynamoDB
    schema_id = "test_1"  # Modify as needed
    db_schema = get_schema_by_id(schema_id)  

    if not db_schema:
        raise ValueError("Could not retrieve schema.") 
    
    system_message = get_system_message(db_schema)

    if not system_message:
         raise ValueError("Could not retrieve system message.") 

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
