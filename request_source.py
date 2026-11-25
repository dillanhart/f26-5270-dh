import logging
from abc import ABC, abstractmethod
from typing import Optional
from botocore.exceptions import ClientError
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ReceivedRequest:
    body: str
    receipt_handle: Optional[str] = None   # S3 requests don't have one

class RequestSource(ABC):
    @abstractmethod
    def get_next_request(self) -> Optional[ReceivedRequest]: ...

    @abstractmethod
    def acknowledge(self, request: ReceivedRequest) -> None: ...

class S3RequestSource(RequestSource):
    def __init__(self, s3_client, bucket_name: str):
        self.s3 = s3_client
        self.bucket = bucket_name

    def get_next_request(self) -> Optional[ReceivedRequest]:
        response = self.s3.list_objects_v2(Bucket=self.bucket, MaxKeys=1)
        contents = response.get("Contents")
        if not contents:
            logger.debug("No requests in %s", self.bucket)
            return None
        key = contents[0]["Key"]
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            text = response["Body"].read().decode("utf-8")
            self.s3.delete_object(Bucket=self.bucket, Key=key)
        except ClientError:
            logger.warning("Request %s disappeared before it could be read", key)
            return None
        logger.info("Retrieved request %s", key)
        return ReceivedRequest(text)

    def acknowledge(self, request: ReceivedRequest) -> None:
        pass  # already deleted when read




class SqsRequestSource(RequestSource):
    def __init__(self, sqs_client, queue_name: str, wait_seconds: int = 20):
        self.sqs = sqs_client
        self.queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
        self.wait_seconds = wait_seconds
        self.cache = deque()          # from collections import deque

    def get_next_request(self) -> Optional[ReceivedRequest]:
        if not self.cache:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=self.wait_seconds,
            )
            for message in response.get("Messages", []):
                # Create a ReceivedRequest object and append it to the cache
                request = ReceivedRequest(
                    body=message.get("Body"),
                    receipt_handle=message.get("ReceiptHandle")
                )
                self.cache.append(request)
        if not self.cache:
            return None
        return self.cache.popleft()

    def acknowledge(self, request: ReceivedRequest) -> None:
        self.sqs.delete_message(QueueUrl=self.queue_url,
                                ReceiptHandle=request.receipt_handle)