# GCS Deploy

**GCS Deploy** is a Python utility to automate the full deployment and destruction of a [Globus Connect Server](https://docs.globus.org/globus-connect-server/) endpoint. It sets up a fully functional endpoint with a storage gateway, identity mapping, and mapped collection—all driven by a single configuration JSON file.

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
- A storage gateway (POSIX)
- A mapped collection


During the deployment process, you will be prompted to log in manually twice to complete the Globus endpoint registration and authentication steps.


### Destroy

```bash
gcs-deploy destroy path/to/config.json
```

This tears down the above setup (in reverse):

- Deletes the mapped collection
- Deletes the storage gateway
- Cleans up the node and endpoint
- Restarts Apache services


During destroy, you will be prompted once for authentication to authorize the removal of the Globus endpoint.



---

## Endpoint Configuration Params: `config.json`

You must provide a JSON file like this:

```json
{
  "endpoint_display_name": "AWS-Endpoint",
  "organization": "The University of Melbourne",
  "owner": "fjimenezibar@unimelb.edu.au",
  "contact_email": "felipe.jimenezibarra@unimelb.edu.au",
  "gateway_name": "My Host Gateway",
  "user_domain": "unimelb.edu.au",
  "collection_name": "My Collection",
  "collection_path": "/home/my-user/",
  "deployment_key_path": "deployment-key.json",
  "identity_mapping": {
    "DATA_TYPE": "expression_identity_mapping#1.0.0",
    "mappings": [
      {
        "source": "{username}",
        "match": ".*@unimelb\.edu\.au",
        "output": "my-user"
      }
    ]
  }
}
```

