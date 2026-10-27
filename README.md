# CS5270 HW6 – Widget Consumer

A Python program that reads Widget Requests from an S3 bucket (Bucket 2), one at a time in key order, and stores the resulting widgets either in another S3 bucket (Bucket 3) or in a DynamoDB table. HW6 handles create requests; update and delete requests are recognized and logged as not yet implemented (HW7).

## Requirements

- Python 3.10 or newer (developed with 3.14)
- AWS credentials configured for the AWS CLI (`aws configure`), with access to the request bucket and to the widget bucket or table
- Java, only for running the instructor-provided `producer.jar`

## Setup

From this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run `source .venv/bin/activate` in each new terminal before using the commands below.

## Running the Consumer

Store widgets in an S3 bucket (Bucket 3):

```bash
python cli.py -rb <request-bucket> -wb <widget-bucket>
```

Store widgets in a DynamoDB table, stopping after 60 seconds:

```bash
python cli.py -rb <request-bucket> -dwt <table-name> -mrt 60000
```

| Option | Meaning | Default |
|---|---|---|
| `-p`, `--profile` | AWS profile for credentials | `default` |
| `-r`, `--region` | AWS region | `us-east-1` |
| `-rb`, `--request-bucket` | Bucket 2, which holds the requests | required |
| `-wb`, `--widget-bucket` | Store widgets in this S3 bucket | one of `-wb` / `-dwt` is required |
| `-dwt`, `--dynamodb-widget-table` | Store widgets in this DynamoDB table | one of `-wb` / `-dwt` is required |
| `-mrt`, `--max-runtime` | Stop after this many milliseconds; `0` runs until Ctrl+C | `0` |
| `-pi`, `--poll-interval` | Milliseconds to wait when no request is available | `100` |
| `-l`, `--log-file` | Log file path | `logs/consumer.log` |
| `-v`, `--verbose` | Log at DEBUG level | off |

`python cli.py --help` prints the same list.

### Where widgets are stored

- **S3:** each widget is saved as JSON at `widgets/{owner}/{widgetId}`, where `{owner}` is the owner's name in lower case with spaces replaced by dashes (`Mary Matthews` → `mary-matthews`).
- **DynamoDB:** the table's partition key must be named `id` (a string). Each entry in `otherAttributes` becomes its own top-level attribute on the item.

### System test with the Producer

Start the Consumer in one terminal, then generate requests in another:

```bash
python cli.py -rb <request-bucket> -wb <widget-bucket> -mrt 60000
java -jar producer.jar -rb <request-bucket> -mwr 10
```

## Running the tests

```bash
pytest tests/ -v
```

The tests use `moto` to fake S3 and DynamoDB, so they don't need AWS credentials or touch real resources.

## Project layout

| File | Responsibility |
|---|---|
| `cli.py` | Parses command-line arguments, sets up logging, builds the components and starts the Consumer |
| `models.py` | `Widget` and `WidgetRequest` data classes, plus conversion to an S3 key, JSON and a DynamoDB item |
| `request_source.py` | `RequestSource` interface and `S3RequestSource`, which reads and deletes the request with the smallest key |
| `widget_store.py` | `WidgetStore` interface, with `S3WidgetStore` and `DynamoWidgetStore` implementations |
| `processor.py` | `RequestProcessor`, which parses a request and dispatches on its type |
| `consumer.py` | `Consumer`, the polling loop: get a request, process it, or wait and try again |
| `tests/` | One pytest file per module |

The request source and widget store are passed into the Consumer as interfaces, so a different source (such as a queue in a later assignment) can be added without changing the Consumer or the processor.

## Credits

This project was developed with help from Claude, an AI assistant by Anthropic:

- `cli.py` was written by Claude, and later extended by me to wire the components together.
- The `Widget` class in `models.py` (S3 key, JSON and DynamoDB conversion) was written by Claude.
- The design of the other modules and their tests was suggested by Claude as code skeletons with blanks, which I completed, debugged and tested myself.

Libraries used: [boto3](https://github.com/boto/boto3) for AWS access, [moto](https://github.com/getmoto/moto) for faking AWS in tests, and [pytest](https://pytest.org) for running the tests.
