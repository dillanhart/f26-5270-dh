import argparse
import logging
import sys
from dataclasses import dataclass
from typing import Optional, Sequence

DEFAULT_PROFILE = "default"
DEFAULT_REGION = "us-east-1"
DEFAULT_POLL_INTERVAL_MS = 100
DEFAULT_LOG_FILE = "logs/consumer.log"

STORAGE_S3 = "s3"
STORAGE_DYNAMODB = "dynamodb"


@dataclass(frozen=True)
class ConsumerConfig:
    profile: str
    region: str
    request_bucket: str
    storage: str
    widget_bucket: Optional[str]
    dynamodb_table: Optional[str]
    max_runtime_ms: int
    poll_interval_ms: int
    log_file: str
    verbose: bool


def _non_negative_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected an integer, got {text!r}")
    if value < 0:
        raise argparse.ArgumentTypeError(f"expected a value >= 0, got {value}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="consumer",
        description="Read widget requests from S3 and store widgets in S3 or DynamoDB.",
        epilog=(
            "examples:\n"
            "  python cli.py -rb usu-cs5270-blue-requests -wb usu-cs5270-blue-web\n"
            "  python cli.py -rb usu-cs5270-blue-requests -dwt widgets -mrt 60000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-p", "--profile", default=DEFAULT_PROFILE,
                        help=f"AWS profile to use for credentials (default={DEFAULT_PROFILE})")
    parser.add_argument("-r", "--region", default=DEFAULT_REGION,
                        help=f"AWS region (default={DEFAULT_REGION})")
    parser.add_argument("-rb", "--request-bucket", required=True,
                        help="Bucket 2: bucket that contains widget requests")

    storage = parser.add_mutually_exclusive_group(required=True)
    storage.add_argument("-wb", "--widget-bucket",
                         help="Bucket 3: store widgets as JSON objects in this bucket")
    storage.add_argument("-dwt", "--dynamodb-widget-table",
                         help="store widgets as items in this DynamoDB table")

    parser.add_argument("-mrt", "--max-runtime", type=_non_negative_int, default=0,
                        help="maximum runtime in milliseconds; 0 runs until interrupted (default=0)")
    parser.add_argument("-pi", "--poll-interval", type=_non_negative_int,
                        default=DEFAULT_POLL_INTERVAL_MS,
                        help=f"milliseconds to wait when no request is available "
                             f"(default={DEFAULT_POLL_INTERVAL_MS})")
    parser.add_argument("-l", "--log-file", default=DEFAULT_LOG_FILE,
                        help=f"path of the log file (default={DEFAULT_LOG_FILE})")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="log at DEBUG level instead of INFO")
    return parser


def parse_args(argv: Optional[Sequence[str]] = None) -> ConsumerConfig:
    args = build_parser().parse_args(argv)
    return ConsumerConfig(
        profile=args.profile,
        region=args.region,
        request_bucket=args.request_bucket,
        storage=STORAGE_S3 if args.widget_bucket else STORAGE_DYNAMODB,
        widget_bucket=args.widget_bucket,
        dynamodb_table=args.dynamodb_widget_table,
        max_runtime_ms=args.max_runtime,
        poll_interval_ms=args.poll_interval,
        log_file=args.log_file,
        verbose=args.verbose,
    )


def configure_logging(config: ConsumerConfig) -> None:
    logging.basicConfig(
        level=logging.DEBUG if config.verbose else logging.INFO,
        format="%(asctime)s [%(threadName)s] %(levelname)s %(name)s - %(message)s",
        handlers=[logging.FileHandler(config.log_file), logging.StreamHandler()],
    )
    for name in ("boto3", "botocore", "s3transfer", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)


def main(argv: Optional[Sequence[str]] = None) -> int:
    config = parse_args(argv)
    configure_logging(config)
    logger = logging.getLogger("consumer.cli")
    for field, value in vars(config).items():
        logger.info("%s: %s", field, value)

    # TODO: build the request source and widget store from `config`
    # and start the consumer's polling loop here.
    return 0


if __name__ == "__main__":
    sys.exit(main())
