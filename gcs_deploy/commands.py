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

