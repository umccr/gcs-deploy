import argparse
from gcs_deploy.commands import (
    load_config,
    setup_endpoint,
    setup_node,
    login_localhost,
    create_storage_gateway,
    create_mapped_collection,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json", help="Path to config file")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them")
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config(args.config)
    setup_endpoint(config, dry_run=args.dry_run)
    setup_node(dry_run=args.dry_run)
    login_localhost(dry_run=args.dry_run)
    create_storage_gateway(config, dry_run=args.dry_run)
    create_mapped_collection(config, dry_run=args.dry_run)



