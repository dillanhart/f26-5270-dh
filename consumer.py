import logging
import time

from processor import RequestProcessor
from request_source import RequestSource

logger = logging.getLogger(__name__)


class Consumer:
    """Polls a RequestSource and hands each request to a RequestProcessor."""

    def __init__(self, source: RequestSource, processor: RequestProcessor,
                 poll_interval_ms: int, max_runtime_ms: int):
        self.source = source
        self.processor = processor
        self.poll_interval_ms = poll_interval_ms
        self.max_runtime_ms = max_runtime_ms

    def run(self) -> int:
        """Run the polling loop. Returns how many requests were processed."""
        start = time.monotonic()
        processed = 0
        logger.info("Consumer started")

        while not self._time_is_up(start):
            text = self.source.get_next_request()
            if text is not None:
                message = self.processor.process(text)
                logger.info(message)
                processed += 1
            else:
                time.sleep(self.poll_interval_ms / 1000)

        logger.info("Consumer stopped after processing %d requests", processed)
        return processed

    def _time_is_up(self, start: float) -> bool:
        """True once max_runtime_ms has passed. A max of 0 means run forever."""
        if self.max_runtime_ms == 0:
            return False
        elapsed_ms = (time.monotonic() - start) * 1000
        return elapsed_ms >= self.max_runtime_ms
