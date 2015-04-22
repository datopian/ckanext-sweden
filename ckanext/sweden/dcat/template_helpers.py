import json


def json_loads(string):
    try:
        return json.loads(string)
    except ValueError:
        return None
