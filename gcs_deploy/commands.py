import subprocess
import json
from pathlib import Path
import shlex

def run_command(cmd, capture_output=False):
    """
    Runs a shell command using subprocess.

    Args:
        cmd (str): The shell command to run.
        capture_output (bool): If True, returns the command's stdout.

    Returns:
        str or None: Output if captured, otherwise None.
    """
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, text=True,
                            capture_output=capture_output)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print("ERR:", result.stderr.strip())
    if capture_output:
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
    
    
def get_gateway_id_by_name(
        name,
        GCS_CLI_CLIENT_ID=None,
        GCS_CLI_CLIENT_SECRET=None,
        GCS_CLI_ENDPOINT_ID=None,
    ):
    """
    Retrieves the storage gateway ID matching the given display name.

    Args:
        name (str): The display name of the storage gateway.

    Returns:
        str: The storage gateway ID (UUID).

    Raises:
        RuntimeError: If the gateway name is not found.
    """

    env_vars = ""
    if GCS_CLI_CLIENT_ID and GCS_CLI_CLIENT_SECRET and GCS_CLI_ENDPOINT_ID:
        env_vars = (
            f"GCS_CLI_CLIENT_ID={GCS_CLI_CLIENT_ID} "
            f"GCS_CLI_CLIENT_SECRET={GCS_CLI_CLIENT_SECRET} "
            f"GCS_CLI_ENDPOINT_ID={GCS_CLI_ENDPOINT_ID} "
        )
    cmd = (
        f"{env_vars}"
        f"globus-connect-server storage-gateway list --format json"
    )
    output = run_command(
        cmd,
        capture_output=True
    )

    try:
        result = json.loads(output)
        gateway_list = result[0]["data"]
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raise RuntimeError("Failed to parse storage-gateway list output") from e

    for gw in gateway_list:
        if gw.get("display_name") == name:
            return gw.get("id")

    raise RuntimeError(f"Gateway with name '{name}' not found.")


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


def create_storage_gateway(config):
    """
    Creates a POSIX storage gateway using the identity mapping file.

    Args:
        config (dict): Must include:
            - gateway_name (str): Human-readable name for the gateway
            - user_domain (str): Identity domain allowed to access it
    """
    gateway_config = config["gateway"]
    gateway_name = gateway_config['gateway_name']
    user_domain = gateway_config["user_domain"]
    identity_mapping = gateway_config["identity_mapping"] 
    # read the identity map from the config:
    identity_mapping_str = json.dumps(identity_mapping)

    # Endpoint info for authentication
    GCS_CLI_CLIENT_ID = config.get("GCS_CLI_CLIENT_ID")
    GCS_CLI_CLIENT_SECRET = config.get("GCS_CLI_CLIENT_SECRET")
    info_path = config["info_path"]
    GCS_CLI_ENDPOINT_ID = read_json(info_path).get("endpoint_id")
    
    cmd = (
        f"GCS_CLI_CLIENT_ID={GCS_CLI_CLIENT_ID} "
        f"GCS_CLI_CLIENT_SECRET={GCS_CLI_CLIENT_SECRET} "
        f"GCS_CLI_ENDPOINT_ID={GCS_CLI_ENDPOINT_ID} "
        f"globus-connect-server storage-gateway create posix "
        f"\"{gateway_name}\" "
        f"--domain {user_domain} "
        f"--identity-mapping '{identity_mapping_str}'"
    )

    print(f">>> Creating storage gateway: {gateway_name}")
    run_command(cmd)



def create_mapped_collection(config):
    """
    Creates a mapped collection for a given storage gateway.

    Args:
        config (dict): Must include:
            - gateway_name (str): Name of the storage gateway to link
            - collection_name (str): Name shown in the Globus Web UI
            - collection_path (str): Local path exposed to users
    """

    # Endpoint info for authentication
    GCS_CLI_CLIENT_ID = config.get("GCS_CLI_CLIENT_ID")
    GCS_CLI_CLIENT_SECRET = config.get("GCS_CLI_CLIENT_SECRET")
    info_path = config["info_path"]
    GCS_CLI_ENDPOINT_ID = read_json(info_path).get("endpoint_id")


    gateway_config = config["gateway"]
    gateway_name = gateway_config['gateway_name']
    gateway_id = get_gateway_id_by_name(
        gateway_name,
        GCS_CLI_CLIENT_ID,
        GCS_CLI_CLIENT_SECRET,
        GCS_CLI_ENDPOINT_ID,
    )

    collection_config = config["collection"]
    collection_name = collection_config['collection_name']
    collection_path = collection_config['collection_path']

    # 1) Create the whole collection path 
    Path(collection_path).mkdir(parents=True, exist_ok=True)

    # 2) Create the mapped collection
    cmd = (
    f"GCS_CLI_CLIENT_ID={GCS_CLI_CLIENT_ID} "
    f"GCS_CLI_CLIENT_SECRET={GCS_CLI_CLIENT_SECRET} "
    f"GCS_CLI_ENDPOINT_ID={GCS_CLI_ENDPOINT_ID} "
    f"globus-connect-server collection create {gateway_id} "
    f"{collection_path} \"{collection_name}\" "
    f"--public"
    )

    print(f">>> Creating mapped collection: {collection_name}")
    run_command(cmd)

def change_endpoint_owner(config):

    endpoint_config = config["endpoint"]
    owner = endpoint_config["owner"]
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
    print(f">>> Changing endpoint owner to: {owner}")
    run_command(cmd)
    # 2) Login to the endpoint
    cmd = (
        f"globus-connect-server login {GCS_CLI_CLIENT_ID} "
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
    


# def login_localhost():
#     """
#     Links the Globus Connect Server to your personal Globus identity.

#     This step opens a browser-based login to authenticate and authorize
#     you as the administrator of the endpoint.
#     """
#     cmd = "globus-connect-server login localhost"
#     print(">>> Logging in to link your Globus identity to the endpoint")
#     run_command(cmd)



def destroy(config):
    """
    Cleans up the Globus Connect Server setup by:
    1. Deleting the mapped collection
    2. Deleting the storage gateway
    3. Cleaning up the endpoint (removes the endpoint config)

    Args:
        config (dict): Must include:
            - collection_name (str): Display name of the mapped collection
            - gateway_name (str): Display name of the storage gateway
            - deployment_key_path (str): Path to deployment key (usually 'deployment-key.json')
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
        gateway_id = get_gateway_id_by_name(gateway_name)
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
        run_command(f"sudo globus-connect-server endpoint cleanup -d {config['deployment_key_path']} --agree-to-delete-endpoint")
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
    run_command("globus-connect-server logout")

