import json
from dataclasses import asdict

import boto3
import pytest
from moto import mock_aws

from models import Widget
from widget_store import DynamoWidgetStore, S3WidgetStore, WidgetStore, WidgetNotFoundError
from botocore.exceptions import ClientError

BUCKET = "test-widgets"
TABLE = "widgets"

WIDGET = Widget(
    widgetId="w1",
    owner="Mary Matthews",
    label="JWJYY",
    description="a test widget",
    otherAttributes=[
        {"name": "rating", "value": "2.5"},
        {"name": "width-unit", "value": "cm"},
    ],
)

WIDGET2 = Widget(
    widgetId="w1",
    owner="John Jacobs",
    label="JWJYY",
    description="a testing widget",
    otherAttributes=[
        {"name": "rating", "value": "2.5"},
        {"name": "width-unit", "value": "cm"},
    ],
)


WIDGET3 = Widget(
    widgetId="w1",
    owner="Mary Matthews",
    otherAttributes=[
        {"name": "rating", "value": "3.5"},
        {"name": "width-unit", "value": "cm"},
    ],
)

def make_dynamo_table():
    """Create a fake DynamoDB table. Only call inside @mock_aws tests."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    return dynamodb.create_table(
        TableName=TABLE,
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

def make_bucket():
    """Create a fake S3 bucket. Only call inside @mock_aws tests."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)
    return s3


@mock_aws
def test_s3_save_writes_json_at_owner_key():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)
    store = S3WidgetStore(s3, BUCKET)


    store.save(WIDGET)


    obj = s3.get_object(Bucket=BUCKET, Key="widgets/mary-matthews/w1")
    saved = json.loads(obj["Body"].read())
    assert saved == asdict(WIDGET)


@mock_aws
def test_dynamo_save_flattens_other_attributes():

    table = make_dynamo_table()
    store = DynamoWidgetStore(table)

    
    store.save(WIDGET)

    
    item = table.get_item(Key={"id": "w1"})["Item"]
    assert item["owner"] == "Mary Matthews"
    assert item["label"] == "JWJYY"
    assert item["rating"] == "2.5"
    assert item["width-unit"] == "cm"
    assert "otherAttributes" not in item

@mock_aws
def test_dynamo_delete_removes_widget():
    table = make_dynamo_table()
    store = DynamoWidgetStore(table)
    store.save(WIDGET)

    store.delete(WIDGET)

    response = table.get_item(Key={"id": "w1"})
    assert "Item" not in response


@mock_aws
def test_dynamo_delete_nothing_raises_error():
    table = make_dynamo_table()
    store = DynamoWidgetStore(table)

    with pytest.raises(WidgetNotFoundError):
        store.delete(WIDGET)



@mock_aws
def test_dynamo_update_updates_widget():
    table = make_dynamo_table()
    store = DynamoWidgetStore(table)
    store.save(WIDGET)

    store.update(WIDGET2)

    item = table.get_item(Key={"id": "w1"})["Item"]
    assert item["owner"] == "John Jacobs"
    assert item["description"] == "a testing widget"


@mock_aws
def test_dynamo_update_doesnt_overwrite_widget():
    table = make_dynamo_table()
    store = DynamoWidgetStore(table)
    store.save(WIDGET)

    store.update(WIDGET3)

    item = table.get_item(Key={"id": "w1"})["Item"]
    assert item["owner"] == "Mary Matthews"
    assert item["label"] == "JWJYY"
    assert item["rating"] == "3.5"
    assert item["width-unit"] == "cm"


@mock_aws
def test_dynamo_update_raises_error_widget():
    table = make_dynamo_table()
    store = DynamoWidgetStore(table)
    with pytest.raises(WidgetNotFoundError):
        store.update(WIDGET)


def test_widget_store_cannot_be_created_directly():
    with pytest.raises(TypeError):
        WidgetStore()


@mock_aws
def test_s3_delete_removes_widget():
    s3 = make_bucket()
    store = S3WidgetStore(s3, BUCKET)
    store.save(WIDGET)

    store.delete(WIDGET)

    with pytest.raises(ClientError):
        s3.head_object(Bucket=BUCKET, Key="widgets/mary-matthews/w1")

@mock_aws
def test_s3_delete_missing_raises_error():
    s3 = make_bucket()
    store = S3WidgetStore(s3, BUCKET)
    with pytest.raises(WidgetNotFoundError):
        store.delete(WIDGET)

@mock_aws
def test_s3_update_replaces_widget():
    s3 = make_bucket()
    store = S3WidgetStore(s3, BUCKET)
    store.save(WIDGET)

    store.update(WIDGET3)

    obj = s3.get_object(Bucket=BUCKET, Key="widgets/mary-matthews/w1")
    saved = json.loads(obj["Body"].read())
    assert saved == asdict(WIDGET3)


@mock_aws
def test_s3_update_missing_raises_error():
    s3 = make_bucket()
    store = S3WidgetStore(s3, BUCKET)
    with pytest.raises(WidgetNotFoundError):
        store.update(WIDGET)