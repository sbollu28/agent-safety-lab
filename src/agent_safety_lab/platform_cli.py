"""Command-line interface for the synthetic network policy platform."""
from __future__ import annotations

import argparse
import json

from .platform import PolicyPlatform, WorkflowError, seed_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline network policy automation demo (NO SSH)")
    parser.add_argument("--db", default="demo-platform.sqlite3", help="Local SQLite database file")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-demo", help="Initialize two synthetic sites and actors")
    submit = sub.add_parser("submit", help="Submit synthetic request")
    submit.add_argument("ticket")
    submit.add_argument("requester")
    submit.add_argument("site")
    submit.add_argument("flow")
    run = sub.add_parser("run", help="Run one simulated polling cycle")
    run.add_argument("--fail-ticket", help="Inject a mock deployment failure")
    roll = sub.add_parser("rollback", help="Manually trigger *simulated* rollback")
    roll.add_argument("engineer")
    roll.add_argument("ticket")
    site = sub.add_parser("onboard-site", help="Add synthetic site address mapping")
    site.add_argument("engineer")
    site.add_argument("site")
    site.add_argument("objects_json", help='e.g. {"monitor":"192.0.2.12","api":"198.51.100.22"}')
    sub.add_parser("status")
    args = parser.parse_args()
    platform = PolicyPlatform(args.db)
    try:
        if args.command == "init-demo":
            seed_demo(platform)
            result = {"status": "initialized", "db": args.db}
        elif args.command == "submit":
            platform.submit(args.ticket, args.requester, args.site, args.flow)
            result = {"submitted": args.ticket}
        elif args.command == "run":
            result = {"processed": platform.run_once(args.fail_ticket)}
        elif args.command == "rollback":
            platform.rollback(args.engineer, args.ticket)
            result = {"manual_rollback_simulated": args.ticket}
        elif args.command == "onboard-site":
            platform.onboard_site(args.engineer, args.site, json.loads(args.objects_json))
            result = {"site_onboarded": args.site}
        else:
            result = platform.snapshot()
        print(json.dumps(result, indent=2))
    except (WorkflowError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(status=2, message=f"Rejected: {exc}\n")
    finally:
        platform.close()


if __name__ == "__main__":
    main()
