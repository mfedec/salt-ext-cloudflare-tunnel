"""
Utility module for common Cloudflare things

:depends: Cloudflare python module
"""
import logging

import salt.exceptions

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


def get_client(api_token):
    """
    Creates a cloudflare object to use for connecting to the api

    api_token
        Cloudflare API token that has permissions to edit cloudflare tunnels
    """
    try:
        client = CloudFlare.CloudFlare(token=api_token)
    except CloudFlare.exceptions.CloudFlareAPIError as exc:
        log.exception(exc)
        raise salt.exceptions.CommandExecutionError(exc)

    return client


def get_zone_id(api_token, domain_name):
    """
    Gets the zone for the specified domain name

    api_token
        Cloudflare API token that has permissions to edit cloudflare tunnels

    domain_name
        domain name to get zone for (something.example.com)
    """
    client = get_client(api_token)

    try:
        zone = client.zones.get(params={"name": domain_name})
    except CloudFlare.exceptions.CloudFlareAPIError as exc:
        log.exception(exc)
        raise salt.exceptions.CommandExecutionError(exc)

    return zone
