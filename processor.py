import json
import logging

from models import WidgetRequest
from widget_store import WidgetStore

logger = logging.getLogger(__name__)


class RequestProcessor:
    """Turns request text into actions on a WidgetStore."""

    def __init__(self, store: WidgetStore):
        self.store = store

    def process(self, request_text: str) -> str:
        """Handle one request. Returns a short message saying what happened."""
        data = json.loads(request_text)
        request = WidgetRequest.from_dict(data)

        match request.type:
            case "create":
                return self.create(request)
            case "update":
                return self.update(request)
            case "delete":
                return self.delete(request)
            case _:
                logger.warning("Unknown request type %s in request %s",
                               request.type, request.requestId)
                return f"Unknown request type {request.type}"

    def create(self, request: WidgetRequest) -> str:
        self.store.save(request.widget)
        return f"Created widget {request.widget.widgetId}"

    def update(self, request: WidgetRequest) -> str:
        # HW7: not required yet
        logger.warning("Update not implemented yet (request %s)", request.requestId)
        return "Update not implemented yet"

    def delete(self, request: WidgetRequest) -> str:
        # HW7: not required yet
        logger.warning("Delete not implemented yet (request %s)", request.requestId)
        return "Delete not implemented yet"
