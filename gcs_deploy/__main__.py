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

 # Flag to control DataDock mapped collection creation (default: skip)
    parser.add_argument(
        "--data-dock",
        dest="data_dock",
        action=argparse.BooleanOptionalAction,  # gives --data-dock / --no-data-dock
        default=False,
        help="Create the DataDock mapped collection during deploy (default: off).",
    )
     
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config(args.config_path)

    if args.command == "deploy":
        setup_endpoint(config)
        setup_node()
        login_localhost()
        create_storage_gateway(config)
        if args.data_dock:
            create_mapped_collection(config) 

    elif args.command == "destroy":
        destroy(config)


if __name__ == "__main__":
    main()
