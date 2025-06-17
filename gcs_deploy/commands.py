import subprocess
import json

def run_command(cmd, capture_output=False, dry_run=False):
    """
    Runs a shell command using subprocess.

    Args:
        cmd (str): The shell command to run.
        capture_output (bool): If True, returns the command's stdout.
        dry_run (bool): If True, only prints the command without executing.

    Returns:
        str or None: Output if captured, otherwise None.
    """
    print(f"\n>>> {cmd}")
    if dry_run:
        print("DRY RUN: Command not executed.")
        return "" if capture_output else None

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
    Loads the config file from the given path.

    Args:
        path (str): Path to the config file.

    Returns:
        dict: Parsed configuration values.
    """
    import json
    with open(path) as f:
        return json.load(f)

def setup_endpoint(config, dry_run=False):
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

def setup_node(dry_run=False):
    """
    Registers the current machine as a Globus Connect Server data transfer node.

    This enables the server to participate in the endpoint's transfer infrastructure.
    """
    cmd = "sudo globus-connect-server node setup"
    print(">>> Registering node")
    run_command(cmd)

def login_localhost(dry_run=False):
    """
    Links the Globus Connect Server to your personal Globus identity.

    This step opens a browser-based login to authenticate and authorize
    you as the administrator of the endpoint.
    """
    cmd = "globus-connect-server login localhost"
    print(">>> Logging in to link your Globus identity to the endpoint")
    run_command(cmd)

def create_storage_gateway(config, dry_run=False):
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



def get_gateway_id_by_name(name, dry_run=False):
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


def create_mapped_collection(config, dry_run=False):
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
