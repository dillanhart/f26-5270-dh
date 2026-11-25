import boto3
import pytest
from moto import mock_aws
from request_source import RequestSource, S3RequestSource


BUCKET = "test-requests"

def make_source():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket = BUCKET)
    return s3, S3RequestSource(s3, BUCKET)

@mock_aws
def test_empty_bucket_returns_none():

    s3, source = make_source()

    result = source.get_next_request()

    assert result is None


@mock_aws
def test_returns_body_and_deletes_it():
    s3, source = make_source()
    s3.put_object(Bucket=BUCKET, Key="1", Body='{"type": "create"}')

    result = source.get_next_request()

    assert result.body == '{"type": "create"}'

    remaining = s3.list_objects_v2(Bucket=BUCKET)
    assert "Contents" not in remaining


@mock_aws
def test_returns_smallest_key_first():

    s3, source = make_source()
    s3.put_object(Bucket=BUCKET, Key="2", Body="two")
    s3.put_object(Bucket=BUCKET, Key="1", Body="one")

    first = source.get_next_request()
    second = source.get_next_request()
    third = source.get_next_request()

    # Check
    assert first.body == "one"
    assert second.body == "two"
    assert third is None


def test_request_source_cannot_be_created_directly():
    with pytest.raises(TypeError):
        RequestSource()


from request_source import ReceivedRequest, RequestSource, S3RequestSource, SqsRequestSource

QUEUE = "test-queue"

def make_sqs_source():
    sqs = boto3.client("sqs", region_name="us-east-1")
    url = sqs.create_queue(QueueName=QUEUE)["QueueUrl"]
    return sqs, url, SqsRequestSource(sqs, QUEUE, wait_seconds=0)

@mock_aws
def test_sqs_empty_queue_returns_none():
    sqs, url, source = make_sqs_source()
    assert source.get_next_request() is None

@mock_aws
def test_sqs_returns_messages_one_at_a_time():
    sqs, url, source = make_sqs_source()
    for body in ["a", "b", "c"]:
        sqs.send_message(QueueUrl=url, MessageBody=body)

    bodies = {source.get_next_request().body for _ in range(3)}

    assert bodies == {"a", "b", "c"}       # a standard queue doesn't guarantee order

@mock_aws
def test_sqs_acknowledge_deletes_message():
    sqs, url, source = make_sqs_source()
    sqs.send_message(QueueUrl=url, MessageBody="a")

    source.acknowledge(source.get_next_request())

    attrs = sqs.get_queue_attributes(QueueUrl=url, AttributeNames=["All"])["Attributes"]
    assert attrs["ApproximateNumberOfMessages"] == "0"
    assert attrs["ApproximateNumberOfMessagesNotVisible"] == "0"