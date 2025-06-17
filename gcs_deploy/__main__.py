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
    parser.add_argument("--config", default="gcs_deploy/config.json", help="Path to config file")
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config(args.config)
    setup_endpoint(config)
    setup_node()
    login_localhost()
    create_storage_gateway(config)
    create_mapped_collection(config)



if __name__ == "__main__":
    main()
