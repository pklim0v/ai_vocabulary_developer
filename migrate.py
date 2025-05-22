import asyncio
import sys
import os
from pathlib import Path

# Importing project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from alembic.config import Config
from alembic import command
from config import get_config

def get_alembic_config():
    alembic_cfg = Config('alembic.ini')
    config = get_config()
    alembic_cfg.set_main_option('sqlalchemy.url', config.DATABASE_URI)
    return alembic_cfg

def create_migration(message: str):
    alembic_cfg = get_alembic_config()
    command.revision(alembic_cfg, message=message, autogenerate=True)
    print(f"Migration {message} created successfully")

def upgrade_database(revision: str = 'head'):
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, revision)
    print(f"Database upgraded to revision {revision}")

def downgrade_database(revision: str):
    alembic_cfg = get_alembic_config()
    command.downgrade(alembic_cfg, revision)
    print(f"Database downgraded to revision {revision}")

def show_current_revision():
    alembic_cfg = get_alembic_config()
    command.current(alembic_cfg)

def show_history():
    alembic_cfg = get_alembic_config()
    command.history(alembic_cfg)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage database migrations")
    subparsers = parser.add_subparsers(dest="command", description="Available commands")

    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("message", help="Migration message")

    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database to the latest revision")
    upgrade_parser.add_argument("revision", default="head", help="Revision to upgrade to (default: head)")

    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database to a specific revision")
    downgrade_parser.add_argument("revision", help="Revision to downgrade to")

    subparsers.add_parser("current", help="Show current database revision")

    subparsers.add_parser('history', help='Show migration history')

    args = parser.parse_args()

    if args.command == "create":
        create_migration(args.message)

    elif args.command == "upgrade":
        upgrade_database(args.revision)

    elif args.command == "downgrade":
        downgrade_database(args.revision)

    elif args.command == "current":
        show_current_revision()

    elif args.command == "history":
        show_history()

    else:
        parser.print_help()



