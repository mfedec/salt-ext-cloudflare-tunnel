"""
Module for managing Cloudflare DNS records

:depends:
    CloudFlare python module
        This module requires the python wrapper for the CloudFlare API.
        https://github.com/cloudflare/python-cloudflare

:configuration: This module can be used by specifying the name of a
    configuration profile in the minion config, minion pillar, or master
    config. The module will use the 'cloudflare' key by default

    For example:

    .. code-block:: yaml

        cloudflare:
            api_token:
            account:


api_token:
    API Token with permissions to create CloudFlare Tunnels

account:
    CloudFlare Account ID, this can be found on the bottom right of the Overview page for your
    domain
"""

import logging

import salt.exceptions
import salt.utils
import saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod as cf_tunnel_utils

try:
    import CloudFlare

    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False

log = logging.getLogger(__name__)

__virtualname__ = "cloudflare_dns"

def __virtual__():
    if HAS_LIBS:
        return __virtualname__

    return (
        False,
        "The cloudflare execution module cannot be loaded: "
        "Cloudflare Python module is not installed.",
    )

def get_dns(record):
    """
    Get dns record details
    """
    print("get dns coming soon.")


def list_dns(domain_name):
    """
    List dns records in zone
    """
    api_token = __salt__["config.get"]("cloudflare").get("api_token")

    zone = cf_tunnel_utils.get_zone_id(api_token, domain_name)

    if zone:
        dns = cf_tunnel_utils.get_dns(api_token, zone[0]["id"])

        print(dns)

        return dns


def create_dns(domain, name, type, content, ttl=1, proxied=True, comment=""):
    """
    Create DNS record

    Note: Add validation TTL Value must be between 60 and 86400, with the minimum reduced to 30 for Enterprise zones.
    
    CLI Example:
    
    .. code-block:: bash

        salt '*' cloudflare_dns.create_dns example.com test A 1.1.1.1 60 True "DNS Managed by SaltStack" 
    
    """
    # Will add more later as I understand more.
    RECORD_TYPES = ["A", "AAAA", "CNAME", "TXT"]
    
    if type in RECORD_TYPES:
        api_token = __salt__["config.get"]("cloudflare").get("api_token")

        zone = cf_tunnel_utils.get_zone_id(api_token, domain)

        if zone:
            dns_data = {
                "name": name,
                "type": type,
                "content": content,
                "ttl": ttl,
                "proxied": proxied,
                "comment": comment
            }
            dns = cf_tunnel_utils.create_dns(api_token, zone[0]["id"], dns_data)
        else:
            raise salt.exceptions.ArgumentValueError(
                f"Cloudflare zone not found for {domain}"
            )
    else:
        raise salt.exceptions.ArgumentValueError(
            f"Not a valid type {type} - must be one of {RECORD_TYPES}"
        )
    
    return dns

# def remove_dns():
