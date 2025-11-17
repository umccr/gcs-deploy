import subprocess
import json
from pathlib import Path
import shlex



def run_command(cmd, capture_output=False):

    result = subprocess.run(
        cmd,
        shell=True, 
        text=True,
        capture_output=capture_output
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print("ERR:", result.stderr.strip())
    if capture_output:
        return result.stdout.strip()


def read_json(path):
    with open(path) as f:
        return json.load(f)
    

def setup_endpoint(config):

    endpoint_config = config["endpoint"]
    display_name = endpoint_config["endpoint_display_name"]
    organization = endpoint_config["organization"]
    contact_email = endpoint_config["contact_email"]
    project_name = endpoint_config["project_name"]
    GCS_CLI_CLIENT_ID = config.get("GCS_CLI_CLIENT_ID")
    GCS_CLI_CLIENT_SECRET = config.get("GCS_CLI_CLIENT_SECRET")

    cmd = (
        f"GCS_CLI_CLIENT_ID={GCS_CLI_CLIENT_ID} "
        f"GCS_CLI_CLIENT_SECRET={GCS_CLI_CLIENT_SECRET} "
        f"globus-connect-server endpoint setup \"{display_name}\" "
        f"--owner \"{GCS_CLI_CLIENT_ID}@clients.auth.globus.org\" "
        f"--project-name \"{project_name}\" "
        f"--organization \"{organization}\" "
        f"--contact-email \"{contact_email}\" "
        f"--agree-to-letsencrypt-tos "
        f"--dont-set-advertised-owner"
    )
    
    print(f">>> Setting up endpoint: {display_name}")
    run_command(cmd)

def setup_node():
    cmd = "sudo globus-connect-server node setup"
    print(">>> Registering node")
    run_command(cmd)



def change_owner(config):

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
    # Step 1: Cleanup local node
    try:
        run_command("sudo globus-connect-server node cleanup")
        print(">>> Node cleanup complete.")
    except Exception as e:
        print(f"!!! Failed to cleanup node: {e}")
    
    # Step 2: Cleanup endpoint
    try:
        run_command(f"sudo globus-connect-server endpoint cleanup --agree-to-delete-endpoint")
        print(">>> Endpoint cleanup complete.")
    except Exception as e:
        print(f"!!! Failed to cleanup endpoint: {e}")

    # Step 3: Restart Apache services
    try:
        run_command("sudo systemctl restart apache2")
        run_command("sudo systemctl reload apache2")
        print(">>> Apache services restarted and reloaded.")
    except Exception as e:
        print(f"!!! Failed to restart Apache: {e}")

    # Step 4: Logout from Globus GCS session    
    print(">>> Logging out of Globus GCS session")
    run_command("globus-connect-server logout --yes")

