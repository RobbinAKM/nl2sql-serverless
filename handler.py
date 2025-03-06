import json
from utils.openai_helper import chat
from utils.db_helper import test_db_connection, get_database_schema


def lambda_handler(event, context):
    body = json.loads(event['body'])
    user_query = body.get("query", "")

    if not user_query:
        return {"statusCode": 400, "body": json.dumps({"error": "Query is required"})}

    history = []
    # Convert Natural Language to SQL
    response, history = chat(user_query, history)

    # if not sql_query:
    #     return {"statusCode": 500, "body": json.dumps({"error": "Failed to generate SQL"})}

    # # Execute SQL Query
    # results = execute_sql(sql_query)

    return {
        "statusCode": 200,
        "body": json.dumps({"db_connected": "True", "query": user_query, "results": response, "history": history,"db_schema":"schema"})
    }
