import json

def handler(event, context):
    """Endpoint that SNS accesses. Includes logic verifying request"""
    print("Fortigate Autoscale Received context: %s", context)
    print("Fortigate Autoscale Received event: " + json.dumps(event, indent=2))
