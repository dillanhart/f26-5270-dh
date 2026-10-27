import json
from dataclasses import dataclass
from typing import Optional, Sequence

def create_request(data):


    return

def delete_request(request):
    return

def change_request(request):
    return


@dataclass(frozen=True)
class widget_request:
    type: str
    requestID: str
    widgetID: str
    owner: str
    label: Optional[str]
    description: Optional[str]
    otherAttributes: Optional[list]



def widget_request(request):
    data = json.loads(request)
    match (data["type"]):
        case "create":
            return create_request(data)
        case "delete":
            return delete_request(data)
        case "change":
            return change_request(data)
        case _:
            return