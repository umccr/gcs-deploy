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
    parser = argparse.ArgumentParser(description="Globus Connect Server deployment tool")
    parser.add_argument("command", choices=["deploy", "destroy"], help="Action to perform")
    parser.add_argument("config_path", help="Path to config file")
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config(args.config_path)

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
