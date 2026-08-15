import argparse

from app import (
    run_search,
    run_classification,
    run_send,
    run_report,
)


def main():
    parser = argparse.ArgumentParser(
        description="Export Automation System"
    )

    subparsers = parser.add_subparsers(
        dest="command"
    )

    # SEARCH
    search_parser = subparsers.add_parser(
        "search",
        help="Search buyer data"
    )
    
    search_parser.add_argument(
        "--query",
        required=True,
        help="Search keyword"
    )

    # CLASSIFY
    subparsers.add_parser(
        "classify",
        help="Classify buyer emails using Gemini"
    )

    # SEND
    send_parser = subparsers.add_parser(
        "send",
        help="Send email campaign"
    )

    send_parser.add_argument(
        "--audience",
        choices=[
            "business",
            "individual",
            "all"
        ],
        default="business"
    )
    
    send_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate sending without actually sending emails"
    )

    # REPORT
    subparsers.add_parser(
        "report",
        help="Show latest report"
    )

    args = parser.parse_args()

    if args.command == "search":
        run_search(args.query)

    elif args.command == "classify":
        run_classification()

    elif args.command == "send":
        run_send(
            args.audience,
            args.dry_run
        )

    elif args.command == "report":
        run_report()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()