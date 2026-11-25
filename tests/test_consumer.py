import time

from consumer import Consumer
from request_source import RequestSource, ReceivedRequest


class FakeSource(RequestSource):
    """Hands out the given strings one at a time, then None forever."""

    def __init__(self, requests):
        self.requests = [ReceivedRequest(text) for text in requests]
        self.acknowledged = []

    def get_next_request(self):
        if self.requests:
            return self.requests.pop(0)
        return None

    def acknowledge(self, request):
        self.acknowledged.append(request)


class FakeProcessor:
    """Remembers every request text it was given."""

    def __init__(self):
        self.received = []

    def process(self, request_text):
        self.received.append(request_text)
        return "ok"


def test_processes_all_requests_in_order():
    source = FakeSource(["a", "b", "c"])
    processor = FakeProcessor()
    consumer = Consumer(source, processor, poll_interval_ms=10, max_runtime_ms=200)


    count = consumer.run()


    assert count == 3
    assert processor.received == ["a", "b", "c"]


def test_empty_source_processes_nothing():
    source = FakeSource([])
    processor = FakeProcessor()
    consumer = Consumer(source, processor, poll_interval_ms=10, max_runtime_ms=50)

    count = consumer.run()

    assert count == 0
    assert processor.received == []


def test_stops_after_max_runtime():
    source = FakeSource([])
    consumer = Consumer(source, FakeProcessor(), poll_interval_ms=10, max_runtime_ms=100)

    started = time.monotonic()
    consumer.run()
    elapsed = time.monotonic() - started


    assert elapsed >= 0.1
    assert elapsed < 0.5


def test_zero_max_runtime_means_never_time_up():
    consumer = Consumer(FakeSource([]), FakeProcessor(), poll_interval_ms=10, max_runtime_ms=0)

    assert consumer._time_is_up(start=0) is False


class FailingProcessor:
    def process(self, request_text):
        raise ValueError("boom")

def test_failed_request_is_still_acknowledged():
    source = FakeSource(["a"])
    consumer = Consumer(source, FailingProcessor(), poll_interval_ms=10, max_runtime_ms=50)

    count = consumer.run()

    assert count == 0
    assert len(source.acknowledged) == 1