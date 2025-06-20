import argparse
from gcs_deploy.commands import (
    load_config,
    setup_endpoint,
    setup_node,
    login_localhost,
    create_storage_gateway,
    create_mapped_collection,
    destroy,
)


def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("deploy", help="Deploy the Globus Connect Server setup")
    subparsers.add_parser("destroy", help="Destroy the existing Globus Connect Server deployment")
    parser.add_argument("--config", default="gcs_deploy/config.json", help="Path to config file")

    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config(args.config)

    if args.command == "deploy":
        setup_endpoint(config)
        setup_node()
        login_localhost()
        create_storage_gateway(config)
        create_mapped_collection(config)

    elif args.command == "destroy":
        destroy(config)


if __name__ == "__main__":
    main()
