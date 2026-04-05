"""Netrc authentication service."""

import os
import netrc
from src.utils.logger import get_logger
logger = get_logger(__name__)

def get_netrc_credentials(machine: str) -> dict[str, str] | None:
    try:
        netrc_path = os.path.expanduser("~/.netrc")
        if not os.path.exists(netrc_path): return None
        auth = netrc.netrc(netrc_path)
        creds = auth.authenticators(machine)
        if creds:
            return {"username": creds[0], "password": creds[2]}
        return None
    except Exception as e:
        logger.warning(f"Netrc auth failed: {e}")
        return None

def build_auth_opts(username: str | None = None, password: str | None = None, netrc_machine: str | None = None) -> dict[str, str]:
    opts: dict[str, str] = {}
    if netrc_machine:
        creds = get_netrc_credentials(netrc_machine)
        if creds:
            opts["username"] = creds["username"]
            opts["password"] = creds["password"]
    if username: opts["username"] = username
    if password: opts["password"] = password
    return opts
