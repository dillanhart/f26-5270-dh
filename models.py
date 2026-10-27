import json
from dataclasses import asdict, dataclass
from typing import Optional


RESERVED_DYNAMODB_NAMES = {"widget_id", "owner", "label", "description"}


@dataclass(frozen=True)
class Widget:
    widgetId: str
    owner: str
    label: Optional[str] = None
    description: Optional[str] = None
    otherAttributes: Optional[list] = None

    def s3_key(self):
        owner_part = self.owner.replace(" ", "-").lower()
        return f"widgets/{owner_part}/{self.widgetId}"

    def to_json(self):
        return json.dumps(asdict(self))

    def to_dynamodb_item(self):
        item = {"widget_id": self.widgetId, "owner": self.owner}
        if self.label:
            item["label"] = self.label
        if self.description:
            item["description"] = self.description
        for attribute in self.otherAttributes or []:
            if attribute["name"] not in RESERVED_DYNAMODB_NAMES:
                item[attribute["name"]] = attribute["value"]
        return item


@dataclass(frozen=True)
class WidgetRequest:
    type: str
    requestId: str
    widget: Widget

    @classmethod
    def from_dict(cls, data):
        # Everything except type and requestId describes the widget itself
        fields = dict(data)
        return cls(
            type=fields.pop("type"),
            requestId=fields.pop("requestId"),
            widget=Widget(**fields),
        )


def widget_request(request):
    data = json.loads(request)
    match (data["type"]):
        case "create":
            return create_request(data)
        case "delete":
            return delete_request(data)
        case "update":
            return update_request(data)
        case _:
            return
