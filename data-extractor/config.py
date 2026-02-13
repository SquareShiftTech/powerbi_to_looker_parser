import os
from dotenv import load_dotenv

load_dotenv()

REQUIRED_VARS = (
    "PBI_TENANT_ID",
    "PBI_WORKSPACE_ID",
    "PBI_CLIENT_ID",
    "PBI_CLIENT_SECRET",
)


def get_config():
    config = {}
    missing = []
    for var in REQUIRED_VARS:
        value = os.getenv(var)
        if not value or not value.strip():
            missing.append(var)
        else:
            config[var] = value.strip()
    if missing:
        raise ValueError(
            f"Missing or empty required environment variables: {', '.join(missing)}. "
             "Set PBI_TENANT_ID, PBI_WORKSPACE_ID, " "PBI_CLIENT_ID, PBI_CLIENT_SECRET."
        )
    return config
