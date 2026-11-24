import logging
from abc import ABC, abstractmethod
from botocore.exceptions import ClientError

from models import Widget

logger = logging.getLogger(__name__)


class WidgetStore(ABC):
    """Somewhere widgets can be saved."""

    @abstractmethod
    def save(self, widget: Widget) -> None:
        ...

    @abstractmethod
    def delete(self, widget: Widget) -> None:
        ...

    @abstractmethod
    def update(self, widget: Widget) -> None:
        ...

class WidgetNotFoundError(Exception): pass

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

    def delete(self, widget: Widget) -> None:
        try: 
            key = widget.s3_key()
            self.s3.head_object(Bucket=self.bucket, Key=key)
            self.s3.delete_object(
                Bucket=self.bucket,
                Key=key
            )
            logger.info("Deleted widget %s from s3://%s/%s", widget.widgetId, self.bucket, key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.warning("Widget delete failed %s", e)
                raise WidgetNotFoundError(f"widget {widget.widgetId} not found") from e
            raise

    def update(self, widget: Widget) -> None:
        try:
            key = widget.s3_key()
            self.s3.head_object(Bucket=self.bucket, Key=key)
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=widget.to_json(),
            )
            logger.info("Updated widget %s in s3://%s/%s", widget.widgetId, self.bucket, key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.warning("Widget update failed %s", e)
                raise WidgetNotFoundError(f"widget {widget.widgetId} not found") from e
            raise


class DynamoWidgetStore(WidgetStore):

    def __init__(self, table):
        self.table = table

    def save(self, widget: Widget) -> None:
            self.table.put_item(Item=widget.to_dynamodb_item())
            logger.info("Saved widget %s to DynamoDB table %s", widget.widgetId, self.table.name)


    def delete(self, widget: Widget) -> None:
        try:
            self.table.delete_item(Key={"id": widget.widgetId}, ConditionExpression="attribute_exists(id)")
            logger.info("Deleted widget %s from DynamoDB table %s", widget.widgetId, self.table.name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                logger.warning("Widget delete failed %s", e)
                raise WidgetNotFoundError(f"widget {widget.widgetId} not found") from e
            raise


    def update(self, widget: Widget) -> None:
        try:
            parts = []
            names = {}
            values = {}
            item = widget.to_dynamodb_item()
            for i, (key, value) in enumerate(item.items()):
                if (key != "id"):
                    parts.append(f"#n{i} = :v{i}") 
                    names[f"#n{i}"] = key
                    values[f":v{i}"] = value
            expression = "Set " + ", ".join(parts)
            self.table.update_item(
                Key={"id": widget.widgetId},
                UpdateExpression=expression,
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
                ConditionExpression="attribute_exists(id)"
            )
            logger.info("Updated widget %s in DynamoDB table %s", widget.widgetId, self.table.name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                logger.warning("Widget update failed %s", e)
                raise WidgetNotFoundError(f"widget {widget.widgetId} not found") from e
            raise