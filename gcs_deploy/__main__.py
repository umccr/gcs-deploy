import argparse
from gcs_deploy.commands import (
    read_json,
    setup_endpoint,
    change_owner,
    setup_node,
    create_storage_gateway,
    create_mapped_collection,
    destroy,
)
import shutil, sys


def parse_args():
    parser = argparse.ArgumentParser(description="Globus Connect Server deployment tool")
    parser.add_argument("command", choices=["deploy", "destroy"], help="Action to perform")
    parser.add_argument("config_path", help="Path to config file")

 # Flag to control DataDock mapped collection creation (default: skip)
    parser.add_argument(
        "--data-dock",
        dest="data_dock",
        action=argparse.BooleanOptionalAction, 
        default=False,
        help="Create the DataDock mapped collection during deploy (default: off).",
    )
     
    return parser.parse_args()



def ensure_gcs_installed():
    if shutil.which("globus-connect-server") is None:
        sys.exit("ERROR: globus-connect-server not found.")


def main():
    args = parse_args()
    ensure_gcs_installed()
    config = read_json(args.config_path)

    if args.command == "deploy":
        setup_endpoint(config)
        setup_node()
        change_owner(config)

    elif args.command == "destroy":
        destroy(config)


if __name__ == "__main__":
    main()
