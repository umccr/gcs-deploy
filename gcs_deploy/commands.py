import subprocess
import json
from pathlib import Path
import shlex

def run_command(cmd, print_stdout=True):

    print(f"\n>>> {cmd}")
    result = subprocess.run(
        cmd,
        shell=True, 
        text=True,
    )
    if print_stdout:
        print(result.stdout.strip())
    # Always print errors    
    if result.stderr:
        print("ERR:", result.stderr.strip())

    return result.stdout.strip()

def read_json(path):
    """
    Loads the config file from a json in the given path.

    Args:
        path (str): Path to the config file.

    Returns:
        dict: Parsed configuration values.
    """
    with open(path) as f:
        return json.load(f)
    
    
def get_id_by_name(
        name,
        type,
        GCS_CLI_CLIENT_ID=None,
        GCS_CLI_CLIENT_SECRET=None,
        GCS_CLI_ENDPOINT_ID=None,
    ):
    
    env_vars = ""
    if GCS_CLI_CLIENT_ID and GCS_CLI_CLIENT_SECRET and GCS_CLI_ENDPOINT_ID:
        env_vars = (
            f"GCS_CLI_CLIENT_ID={GCS_CLI_CLIENT_ID} "
            f"GCS_CLI_CLIENT_SECRET={GCS_CLI_CLIENT_SECRET} "
            f"GCS_CLI_ENDPOINT_ID={GCS_CLI_ENDPOINT_ID} "
        )

    if type == "gateway":    
        cmd = (
            f"{env_vars}"
            f"globus-connect-server storage-gateway list --format json"
        )
        output_with_envelop = run_command(
            cmd,
            capture_output=True
        )
        
        output_with_envelop_json = json.loads(output_with_envelop)
        gateway_list = output_with_envelop_json[0]["data"]

        for gateway in gateway_list:
            gateway_name = gateway["display_name"]
            gateway_id = gateway["id"]
            if gateway_name == name:
                return gateway_id
        

    elif type == "collection":
        cmd = (
            f"{env_vars}"
            f"globus-connect-server collection list --format json"
        )

        output = run_command(
            cmd,
            capture_output=True
        )

        collection_list = json.loads(output)

        for collection in collection_list:
            collection_name = collection["display_name"]
            collection_id = collection["id"]
            if collection_name == name:
                return collection_id
        
    else:
        raise ValueError(f"Unknown type: {type}")

def setup_endpoint(config):
    """
    Sets up the Globus Connect Server endpoint with metadata.

    Args:
        config (dict): Must include the following keys:
            - endpoint_display_name (str)
            - organization (str)
            - owner (str)
            - contact_email (str)
            - project_id (str): Globus Project UUID under which to register the endpoint

    """
    endpoint_config = config["endpoint"]
    display_name = endpoint_config["endpoint_display_name"]
    organization = endpoint_config["organization"]
    contact_email = endpoint_config["contact_email"]
    project_name = endpoint_config["project_name"]
    project_id = endpoint_config["project_id"]
    private = endpoint_config["private"]
    GCS_CLI_CLIENT_ID = config.get("GCS_CLI_CLIENT_ID")
    GCS_CLI_CLIENT_SECRET = config.get("GCS_CLI_CLIENT_SECRET")

    cmd = (
        f"GCS_CLI_CLIENT_ID={GCS_CLI_CLIENT_ID} "
        f"GCS_CLI_CLIENT_SECRET={GCS_CLI_CLIENT_SECRET} "
        f"globus-connect-server endpoint setup \"{display_name}\" "
        f"--owner \"{GCS_CLI_CLIENT_ID}@clients.auth.globus.org\" "
        f"--project-id \"{project_id}\" "
        f"--organization \"{organization}\" "
        f"--contact-email \"{contact_email}\" "
        f"--agree-to-letsencrypt-tos "
        f"--dont-set-advertised-owner"
    )
    
    print(f">>> Setting up endpoint: {display_name}")
    run_command(cmd)

def setup_node():
    """
    Registers the current machine as a Globus Connect Server data transfer node.

    This enables the server to participate in the endpoint's transfer infrastructure.
    """
    cmd = "sudo globus-connect-server node setup"
    print(">>> Registering node")
    run_command(cmd)



def change_owner(config):

    endpoint_config = config["endpoint"]
    owner = endpoint_config["owner"]
    client_id = endpoint_config["client-id"]
    subscription_id = config["subscription-id"]

    # Endpoint info for authentication
    GCS_CLI_CLIENT_ID = config.get("GCS_CLI_CLIENT_ID")
    GCS_CLI_CLIENT_SECRET = config.get("GCS_CLI_CLIENT_SECRET")
    info_path = config["info_path"]
    GCS_CLI_ENDPOINT_ID = read_json(info_path).get("endpoint_id")
  
    # 1) Change endpoint owner
    cmd = (
        f"GCS_CLI_CLIENT_ID={GCS_CLI_CLIENT_ID} "
        f"GCS_CLI_CLIENT_SECRET={GCS_CLI_CLIENT_SECRET} "
        f"GCS_CLI_ENDPOINT_ID={GCS_CLI_ENDPOINT_ID} "
        f"globus-connect-server endpoint set-owner {owner}"
    )
    run_command(cmd)

    # 2) Login to the endpoint
    cmd = (
        f"globus-connect-server login localhost"
    )
    run_command(cmd)
    # 3) Set owner string (Advertised Owner)
    cmd = ( 
        f"globus-connect-server endpoint set-owner-string {owner}"
    )
    run_command(cmd)
    # 4) Set subscription id and make endpoint private
    cmd = ( 
        f"globus-connect-server endpoint update --private --subscription-id {subscription_id}"
    )
    run_command(cmd)

def destroy(config):
    """
    Cleans up the Globus Connect Server setup by:
    1. Deleting all the mapped collection
    2. Deleting all the storage gateway
    3. Cleaning up the endpoint (removes the endpoint config)

    """

    collection_config = config["collection"]
    collection_name = collection_config['collection_name']

    gateway_config = config["gateway"]
    gateway_name = gateway_config['gateway_name']

    # Step 1: Delete the mapped collection
    try:
        collections_out = run_command(
            "globus-connect-server collection list --format json",
            capture_output=True
        )
        collections = json.loads(collections_out)
        collection_id = next(
            c["id"] for c in collections if c["display_name"] == collection_name
        )
        run_command(f"globus-connect-server collection update {collection_id} --no-delete-protected")
        run_command(f"globus-connect-server collection delete {collection_id}")
        print(f">>> Collection '{collection_name}' deleted.")
    except Exception as e:
        print(f"!!! Failed to delete collection: {e}")

    # Step 2: Delete the storage gateway
    try:
        gateway_id = get_id_by_name(gateway_name,"gateway")
        run_command(f"globus-connect-server storage-gateway delete {gateway_id}")
        print(f">>> Storage gateway '{gateway_name}' deleted.")
    except Exception as e:
        print(f"!!! Failed to delete storage gateway: {e}")

    # Step 3: Cleanup local node
    try:
        run_command("sudo globus-connect-server node cleanup")
        print(">>> Node cleanup complete.")
    except Exception as e:
        print(f"!!! Failed to cleanup node: {e}")
    
    # Step 4: Cleanup endpoint
    try:
        run_command(f"sudo globus-connect-server endpoint cleanup --agree-to-delete-endpoint")
        print(">>> Endpoint cleanup complete.")
    except Exception as e:
        print(f"!!! Failed to cleanup endpoint: {e}")

    # Step 5: Restart Apache services
    try:
        run_command("sudo systemctl restart apache2")
        run_command("sudo systemctl reload apache2")
        print(">>> Apache services restarted and reloaded.")
    except Exception as e:
        print(f"!!! Failed to restart Apache: {e}")

    # Step 6: Logout from Globus GCS session    
    print(">>> Logging out of Globus GCS session")
    run_command("globus-connect-server logout --yes")

