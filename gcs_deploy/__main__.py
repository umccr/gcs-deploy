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
    parser.add_argument("--config", default="gcs_deploy/config.json", help="Path to config file")
    parser.add_argument("--destroy", action="store_true", help="Tear down the existing Globus Connect Server deployment")

    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config(args.config)


    if args.destroy:
        destroy(config)
    else:
        args = parse_args()
        config = load_config(args.config)
        setup_endpoint(config)
        setup_node()
        login_localhost() 
        create_storage_gateway(config)
        create_mapped_collection(config)


if __name__ == "__main__":
    main()
