"""
Utility module for managing Cloudflare DNS records

:depends: Cloudflare python module
"""
import logging

import salt.exceptions
import saltext.cloudflare_tunnel.utils.cloudflare_mod as cf_utils

try:
    import CloudFlare

    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False

log = logging.getLogger(__name__)

__virtualname__ = "cloudflare_dns"


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


def get_dns(api_token, zone_id, dns_name=""):
    """
    Get dns entry details

    api_token
        Cloudflare API token that has permissions to edit cloudflare tunnels

    zone_id
        Cloudflare Zone ID

    dns_name
        DNS record name (something.example.com)
    """
    client = cf_utils.get_client(api_token)

    try:
        dns = client.zones.dns_records.get(zone_id, params={"name": dns_name})
    except CloudFlare.exceptions.CloudFlareAPIError as exc:
        log.exception(exc)
        raise salt.exceptions.CommandExecutionError(exc)

    return dns


def create_dns(api_token, zone_id, dns_data, dns_id=None):
    """
    Create a cloudflare dns entry

    api_token
        Cloudflare API token that has permissions to edit cloudflare tunnels

    zone_id
        Cloudflare Zone ID

    dns_data
        dns configuration in json format
        See: https://api.cloudflare.com/#dns-records-for-a-zone-create-dns-record

        {
            "name": "",
            "type": "",
            "content": "",
            "ttl": "",
            "proxied": "",
            "comment": ""
        }

    dns_id
        ID of the DNS entry to remove
        This argument is optional. If supplied then it will edit a dns entry
    """
    client = cf_utils.get_client(api_token)

    try:
        if dns_id:
            dns = client.zones.dns_records.put(zone_id, dns_id, data=dns_data)
        else:
            dns = client.zones.dns_records.post(zone_id, data=dns_data)
    except CloudFlare.exceptions.CloudFlareAPIError as exc:
        log.exception(exc)
        raise salt.exceptions.CommandExecutionError(exc)

    return dns


def remove_dns(api_token, zone_id, dns_id):
    """
    Remove a cloudflare dns entry

    api_token
        Cloudflare API token that has permissions to edit cloudflare tunnels

    zone_id
        Cloudflare Zone ID

    dns_id
        ID of the DNS entry to remove
    """
    client = cf_utils.get_client(api_token)

    try:
        dns = client.zones.dns_records.delete(zone_id, dns_id)
    except CloudFlare.exceptions.CloudFlareAPIError as exc:
        log.exception(exc)
        raise salt.exceptions.CommandExecutionError(exc)

    return dns
