# GCS Deploy

**GCS Deploy** is a Python utility to automate the deployment and destruction of a [Globus Connect Server](https://docs.globus.org/globus-connect-server/) endpoint. It sets up a Globus endpoint with a registered node—all driven by a single configuration JSON file.

⚠️ Globus Connect Server v5 (https://docs.globus.org/globus-connect-server/v5/) is assumed to be installed on the target system.


---

## Installation

Prerequisite: Globus Connect Server v5 

### User Installation

For typical usage:

```bash
pip install .
```

Once installed, the CLI command `gcs-deploy` becomes available.

### Development (Editable) Installation

If you're actively developing this package:

```bash
pip install -e .
```

This allows local code edits to immediately affect the installed command.

---

## Usage

### Deploy

```bash
gcs-deploy deploy path/to/config.json
```

This sets up:

- A Globus endpoint
- A registered node
- Changes the endpoint owner


During the deployment process, you will be prompted to log in manually multiple times to complete the Globus endpoint registration and authentication steps.


### Destroy

```bash
gcs-deploy destroy path/to/config.json
```

This tears down the setup:

- Cleans up the node
- Cleans up the endpoint
- Restarts Apache services
- Logs out of Globus GCS session


During destroy, you will be prompted for authentication to authorize the removal of the Globus endpoint.



---

## Endpoint Configuration Params: `config.json`

You must provide a JSON file like this:

```json
{
  "endpoint": {
    "endpoint_display_name": "AWS-Endpoint",
    "organization": "The University of Melbourne",
    "owner": "user@unimelb.edu.au",
    "contact_email": "contact@unimelb.edu.au",
    "project_name": "Project Name"
  },
  "deployment_key_path": "deployment-key.json", 
  "info_path": "/var/lib/globus-connect-server/info.json",
  "GCS_CLI_CLIENT_ID": "your-client-id",
  "GCS_CLI_CLIENT_SECRET": "your-client-secret",
  "subscription-id": "your-subscription-id"
}
```

### Configuration Parameters

- **endpoint**: Object containing endpoint configuration
  - **endpoint_display_name**: The display name for your Globus endpoint
  - **organization**: Your organization name
  - **owner**: Email address of the endpoint owner
  - **contact_email**: Contact email for the endpoint
  - **project_name**: Name of the project for this endpoint

- **info_path**: Path to the Globus Connect Server info file (typically `/var/lib/globus-connect-server/info.json`)
- **deployment_key_path**: Path where the deployment key JSON file is stored (for example, `deployment-key.json` alongside your config file)
- **GCS_CLI_CLIENT_ID**: Globus client ID for authentication
- **GCS_CLI_CLIENT_SECRET**: Globus client secret for authentication
- **subscription-id**: The Globus subscription UUID 
