"""
Utility module for connecting to Cloudflare to manage Zero Trust Tunnels

:depends: Cloudflare python module
"""
import base64
import logging
import random
import string

import salt.exceptions
import saltext.cloudflare_tunnel.utils.cloudflare_mod as cf_utils
import saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod as cf_tunnel_utils

try:
    import CloudFlare

    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False

log = logging.getLogger(__name__)

__virtualname__ = "cloudflare_tunnel"


def __virtual__():
    """
    Check to make sure cloudflare python installed
    """

    if HAS_LIBS:
        return __virtualname__

    return (
        False,
        "Cloudflare Python module is not installed.",
    )


def _generate_secret():
    """
    Generates a secret to be used when creating the tunnel
    """
    random_string = "".join(
        random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=35)
    )
    random_string_bytes = random_string.encode("ascii")
    base64_string_bytes = base64.b64encode(random_string_bytes)
    base64_string = base64_string_bytes.decode("ascii")

    return base64_string


def get_tunnel_token(api_token, account, tunnel_id):
    """
    Gets the token used to associate cloudflared with a specific tunnel

    api_token
        Cloudflare API token that has permissions to edit cloudflare tunnels

    account
        Cloudflare Account ID

    tunnel_id
        ID of the tunnel
    """
    client = cf_utils._get_client(api_token)

    try:
        token = client.accounts.cfd_tunnel.token.get(account, tunnel_id)
    except CloudFlare.exceptions.CloudFlareAPIError as exc:
        log.exception(exc)
        raise salt.exceptions.CommandExecutionError(exc)

    return token


def get_tunnel(api_token, account, tunnel_name):
    """
    Get a tunnel by name

    api_token
        Cloudflare API token that has permissions to edit cloudflare tunnels

    account
        Cloudflare Account ID

    tunnel_name
        Name for the new tunnel
    """
    client = cf_utils._get_client(api_token)

    try:
        tunnel = client.accounts.cfd_tunnel.get(
            account, params={"name": tunnel_name, "is_deleted": "false"}
        )
    except CloudFlare.exceptions.CloudFlareAPIError as exc:
        log.exception(exc)
        raise salt.exceptions.CommandExecutionError(exc)

    return tunnel


def create_tunnel(api_token, account, tunnel_name):
    """
    Create a new tunnel

    api_token
        Cloudflare API token that has permissions to edit cloudflare tunnels

    account
        Cloudflare Account ID

    tunnel_name
        Name for the new tunnel
    """
    client = cf_utils._get_client(api_token)

    try:
        tunnel = client.accounts.cfd_tunnel.post(
            account,
            data={
                "name": tunnel_name,
                "tunnel_secret": _generate_secret(),
                "config_src": "cloudflare",
            },
        )
    except CloudFlare.exceptions.CloudFlareAPIError as exc:
        log.exception(exc)
        raise salt.exceptions.CommandExecutionError(exc)

    return tunnel


def remove_tunnel(api_token, account, tunnel_id):
    """
    Remove tunnel for the given tunnel_id

    api_token
        Cloudflare API token that has permissions to edit cloudflare tunnels

    account
        Cloudflare Account ID

    tunnel_id
        ID of the tunnel
    """
    client = cf_utils._get_client(api_token)

    try:
        tunnel = client.accounts.cfd_tunnel.delete(account, tunnel_id)
    except CloudFlare.exceptions.CloudFlareAPIError as exc:
        log.exception(exc)
        raise salt.exceptions.CommandExecutionError(exc)

    return tunnel


def get_tunnel_config(api_token, account, tunnel_id):
    """
    Get the config for the given tunnel_id

    api_token
        Cloudflare API token that has permissions to edit cloudflare tunnels

    account
        Cloudflare Account ID

    tunnel_id
        ID of the Cloudflare tunnel
    """
    client = cf_utils._get_client(api_token)

    try:
        tunnel_config = client.accounts.cfd_tunnel.configurations.get(account, tunnel_id)
    except CloudFlare.exceptions.CloudFlareAPIError as exc:
        log.exception(exc)
        raise salt.exceptions.CommandExecutionError(exc)

    return tunnel_config


def create_tunnel_config(api_token, account, tunnel_id, config):
    """
    Create a Cloudflare Tunnel configuration for the given tunnel_id

    api_token
        Cloudflare API token that has permissions to edit cloudflare tunnels

    account
        Cloudflare Account ID

    tunnel_id
        ID of the Cloudflare tunnel

    config
        The tunnel configuration and ingress rules in JSON format
        See: https://api.cloudflare.com/#cloudflare-tunnel-configuration-properties
    """
    client = cf_utils._get_client(api_token)

    try:
        tunnel_config = client.accounts.cfd_tunnel.configurations.put(
            account, tunnel_id, data=config
        )
    except CloudFlare.exceptions.CloudFlareAPIError as exc:
        log.exception(exc)
        raise salt.exceptions.CommandExecutionError(exc)

    return tunnel_config
