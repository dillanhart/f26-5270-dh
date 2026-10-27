import json
from dataclasses import asdict

import boto3
import pytest
from moto import mock_aws

from models import Widget
from widget_store import DynamoWidgetStore, S3WidgetStore, WidgetStore

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


def make_dynamo_table():
    """Create a fake DynamoDB table. Only call inside @mock_aws tests."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    return dynamodb.create_table(
        TableName=TABLE,
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


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


def test_widget_store_cannot_be_created_directly():
    with pytest.raises(TypeError):
        WidgetStore()
