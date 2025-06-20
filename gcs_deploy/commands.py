import subprocess
import json

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

def load_config(path="config.json"):
    """
    Loads the config file from a json in the given path.

    Args:
        path (str): Path to the config file.

    Returns:
        dict: Parsed configuration values.
    """
    import json
    with open(path) as f:
        return json.load(f)

def setup_endpoint(config):
    """
    Sets up the Globus Connect Server endpoint with metadata.

    Args:
        config (dict): Must include the following keys:
            - endpoint_display_name (str)
            - organization (str)
            - owner (str)
            - contact_email (str)
    """
    cmd = (
        f"globus-connect-server endpoint setup \"{config['endpoint_display_name']}\" "
        f"--organization \"{config['organization']}\" "
        f"--owner \"{config['owner']}\" "
        f"--contact-email \"{config['contact_email']}\""
    )
    print(f">>> Setting up endpoint: {config['endpoint_display_name']}")
    run_command(cmd)

def setup_node():
    """
    Registers the current machine as a Globus Connect Server data transfer node.

    This enables the server to participate in the endpoint's transfer infrastructure.
    """
    cmd = "sudo globus-connect-server node setup"
    print(">>> Registering node")
    run_command(cmd)

def login_localhost():
    """
    Links the Globus Connect Server to your personal Globus identity.

    This step opens a browser-based login to authenticate and authorize
    you as the administrator of the endpoint.
    """
    cmd = "globus-connect-server login localhost"
    print(">>> Logging in to link your Globus identity to the endpoint")
    run_command(cmd)

def create_storage_gateway(config):
    """
    Creates a POSIX storage gateway using the identity mapping file.

    Args:
        config (dict): Must include:
            - gateway_name (str): Human-readable name for the gateway
            - user_domain (str): Identity domain allowed to access it
    """
    cmd = (
        f"globus-connect-server storage-gateway create posix "
        f"\"{config['gateway_name']}\" "
        f"--domain {config['user_domain']} "
        f"--identity-mapping file:gcs_deploy/identity_mapping.json"
    )
    print(f">>> Creating storage gateway: {config['gateway_name']}")
    run_command(cmd)



def get_gateway_id_by_name(name):
    """
    Retrieves the storage gateway ID matching the given display name.

    Args:
        name (str): The display name of the storage gateway.

    Returns:
        str: The storage gateway ID (UUID).

    Raises:
        RuntimeError: If the gateway name is not found.
    """
    output = run_command(
        "globus-connect-server storage-gateway list --format json",
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


def create_mapped_collection(config):
    """
    Creates a mapped collection for a given storage gateway.

    Args:
        config (dict): Must include:
            - gateway_name (str): Name of the storage gateway to link
            - collection_name (str): Name shown in the Globus Web UI
            - collection_path (str): Local path exposed to users
    """
    gateway_id = get_gateway_id_by_name(config["gateway_name"])
    cmd = (
        f"globus-connect-server collection create {gateway_id} "
        f"{config['collection_path']} \"{config['collection_name']}\" "
        f"--public"
    )
    print(f">>> Creating mapped collection: {config['collection_name']}")
    run_command(cmd)


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
    # Step 1: Delete the mapped collection
    try:
        collections_out = run_command(
            "globus-connect-server collection list --format json",
            capture_output=True
        )
        collections = json.loads(collections_out)
        collection_id = next(
            c["id"] for c in collections if c["display_name"] == config["collection_name"]
        )
        run_command(f"globus-connect-server collection update {collection_id} --no-delete-protected")
        run_command(f"globus-connect-server collection delete {collection_id}")
        print(f">>> Collection '{config['collection_name']}' deleted.")
    except Exception as e:
        print(f"!!! Failed to delete collection: {e}")

    # Step 2: Delete the storage gateway
    try:
        gateway_id = get_gateway_id_by_name(config["gateway_name"])
        run_command(f"globus-connect-server storage-gateway delete {gateway_id}")
        print(f">>> Storage gateway '{config['gateway_name']}' deleted.")
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
        run_command(f"sudo globus-connect-server endpoint cleanup -d {config['deployment_key_path']}")
        print(">>> Endpoint cleanup complete.")
    except Exception as e:
        print(f"!!! Failed to cleanup endpoint: {e}")

    # Step 5: Logout from Globus GCS session    
    print(">>> Logging out of Globus GCS session")
    run_command("globus-connect-server logout")

    # Step 6: Restart Apache services
    try:
        run_command("sudo systemctl restart apache2")
        run_command("sudo systemctl reload apache2")
        print(">>> Apache services restarted and reloaded.")
    except Exception as e:
        print(f"!!! Failed to restart Apache: {e}")
