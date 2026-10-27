import logging
from abc import ABC, abstractmethod
from typing import Optional
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)

class RequestSource(ABC):
    @abstractmethod
    def get_next_request(self) -> Optional[str]:
        return None

class S3RequestSource(RequestSource):
    def __init__(self, s3_client, bucket_name: str):
        self.s3 = s3_client
        self.bucket = bucket_name

    def get_next_request(self) -> Optional[str]:
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
        return text

