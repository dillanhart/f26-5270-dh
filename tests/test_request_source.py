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

    assert result == '{"type": "create"}'

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
    assert first == "one"
    assert second == "two"
    assert third is None


def test_request_source_cannot_be_created_directly():
    with pytest.raises(TypeError):
        RequestSource()