import logging
from abc import ABC, abstractmethod

from models import Widget

logger = logging.getLogger(__name__)


class WidgetStore(ABC):
    """Somewhere widgets can be saved."""

    @abstractmethod
    def save(self, widget: Widget) -> None:
        ...


class S3WidgetStore(WidgetStore):

    def __init__(self, s3_client, bucket_name: str):
        self.s3 = s3_client
        self.bucket = bucket_name

    def save(self, widget: Widget) -> None:
        key = widget.s3_key()
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=widget.to_json(),
        )
        logger.info("Saved widget %s to s3://%s/%s", widget.widgetId, self.bucket, key)


class DynamoWidgetStore(WidgetStore):

    def __init__(self, table):
        self.table = table

    def save(self, widget: Widget) -> None:
        self.table.put_item(Item=widget.to_dynamodb_item())
        logger.info("Saved widget %s to DynamoDB table %s", widget.widgetId, self.table.name)
