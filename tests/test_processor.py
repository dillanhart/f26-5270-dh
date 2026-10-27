import json

from models import Widget
from processor import RequestProcessor
from widget_store import WidgetStore


class FakeStore(WidgetStore):
    """Pretends to be a store; just remembers every widget it was given."""

    def __init__(self):
        self.saved = []

    def save(self, widget: Widget) -> None:
        self.saved.append(widget)


def make_request_text(request_type):
    """Build the JSON text of a request, like the request source would return."""
    return json.dumps({
        "type": request_type,
        "requestId": "r1",
        "widgetId": "w1",
        "owner": "Mary Matthews",
        "label": "JWJYY",
    })


def test_create_saves_widget():

    store = FakeStore()
    processor = RequestProcessor(store)


    message = processor.process(make_request_text("create"))


    assert len(store.saved) == 1
    assert store.saved[0].widgetId == "w1"
    assert store.saved[0].owner == "Mary Matthews"
    assert "Created" in message


def test_update_saves_nothing():
    store = FakeStore()
    processor = RequestProcessor(store)

    message = processor.process(make_request_text("update"))

    assert store.saved == []
    assert "not implemented" in message


def test_delete_saves_nothing():
    store = FakeStore()
    processor = RequestProcessor(store)

    message = processor.process(make_request_text("delete"))

    assert store.saved == []
    assert "not implemented" in message


def test_unknown_type_saves_nothing():
    store = FakeStore()
    processor = RequestProcessor(store)

    message = processor.process(make_request_text("banana"))

    assert store.saved == []
    assert "Unknown" in message
