import json

def handler(event, context):
    print("MDW Received event: " + json.dumps(event, indent=2))
    return event
