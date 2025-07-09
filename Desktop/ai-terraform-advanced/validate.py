import json

def validate_variables(data: dict, required_keys: list) -> bool:
    for key in required_keys:
        if key not in data or not data[key]:
            print(f"❌ Missing or empty key: {key}")
            return False
    return True
