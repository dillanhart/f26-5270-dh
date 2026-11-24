import json

from models import Widget
from processor import RequestProcessor
from widget_store import WidgetStore


class FakeStore(WidgetStore):
    """Pretends to be a store; just remembers every widget it was given."""

    def __init__(self):
        self.saved = []
        self.deleted = []
        self.updated = []

    def save(self, widget): self.saved.append(widget)
    def delete(self, widget): self.deleted.append(widget)
    def update(self, widget): self.updated.append(widget)


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


def test_delete_deletes_widget():
    store = FakeStore()
    processor = RequestProcessor(store)

    message = processor.process(make_request_text("delete"))

    assert len(store.deleted) == 1
    assert store.deleted[0].widgetId == "w1"
    assert store.saved == []
    assert "Deleted" in message

def test_update_updates_widget():
    store = FakeStore()
    processor = RequestProcessor(store)

    message = processor.process(make_request_text("update"))

    assert len(store.updated) == 1
    assert store.updated[0].widgetId == "w1"
    assert store.updated[0].owner == "Mary Matthews"
    assert store.saved == []
    assert "Updated" in message

def test_unknown_type_saves_nothing():
    store = FakeStore()
    processor = RequestProcessor(store)

    message = processor.process(make_request_text("banana"))

    assert store.saved == []
    assert "Unknown" in message

    