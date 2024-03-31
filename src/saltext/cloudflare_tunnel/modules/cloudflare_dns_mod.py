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
    API Token with permissions to create CloudFlare DNS Records

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


def _simple_zone(zone):
    """
    Simplify the results returned from the API
    """
    return {"id": zone["id"], "name": zone["name"], "status": zone["status"]}


def _simple_dns(dns):
    """
    Simplify the results returned from the API
    """
    return {
        "id": dns["id"],
        "name": dns["name"],
        "type": dns["type"],
        "content": dns["content"],
        "proxied": dns["proxied"],
        "zone_id": dns["zone_id"],
        "comment": dns["comment"],
    }


def _get_zone_id(domain_name):
    """
    Gets the Zone ID from supplied domain name.

    Zone ID is used in the majority of cloudflare api calls. It is the unique ID
    for each domain that is hosted

    domain_name
        Domain name of the zone_id you want to get
    """
    api_token = __salt__["config.get"]("cloudflare").get("api_token")

    zone_details = None
    # Split the dns name to pull out just the domain name to grab the zone id
    domain_split = domain_name.split(".")
    domain_length = len(domain_split)
    domain = f"{domain_split[domain_length - 2]}.{domain_split[domain_length - 1]}"

    zone_details = cf_tunnel_utils.get_zone_id(api_token, domain)

    if zone_details:
        ret_zone_details = {}
        ret_zone_details = _simple_zone(zone_details[0])
    else:
        return False

    return ret_zone_details


def get_dns(dns_name):
    """
    Get DNS details for the supplied dns name

    dns_name
        DNS record name

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_dns.get_dns sample.example.com

    Returns a dictionary containing the dns details or ``False`` if it does not exist
    """
    api_token = __salt__["config.get"]("cloudflare").get("api_token")
    zone = _get_zone_id(dns_name)

    if zone:
        dns = cf_tunnel_utils.get_dns(api_token, zone["id"], dns_name)

        if dns:
            dns_details = {}
            dns_details = dns[0]
        else:
            return False
    else:
        raise salt.exceptions.ArgumentValueError(f"Zone not found for dns {dns_name}")

    return _simple_dns(dns_details)


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


def create_dns(hostname, type, content, ttl=1, proxied=True, comment=""):
    """
    Create DNS record

    Currently supported records: A, AAAA, CNAME, TXT

    Note: Add validation TTL Value must be between 60 and 86400, with the minimum reduced to 30 for Enterprise zones.
    
    CLI Example:
    
    .. code-block:: bash

        salt '*' cloudflare_dns.create_dns test.example.com A 1.1.1.1 60 True "DNS Managed by SaltStack" 
    
    """
    # Will add more later as I understand more.
    RECORD_TYPES = ["A", "AAAA", "CNAME", "TXT"]

    dns = ""
    
    if type in RECORD_TYPES:
        api_token = __salt__["config.get"]("cloudflare").get("api_token")

        zone = _get_zone_id(hostname)

        if zone:
            # Split the dns name to pull out just the domain name to grab the zone id
            
            domain_split = hostname.split(".")
            dns = get_dns(hostname)

            dns_data = {
                "name": domain_split[0],
                "type": type,
                "content": content,
                "ttl": ttl,
                "proxied": proxied,
                "comment": comment
            }
            if dns:
                if dns["content"] != content:
                    dns = cf_tunnel_utils.create_dns(api_token, zone["id"], dns_data, dns["id"])
            else:
                dns = cf_tunnel_utils.create_dns(api_token, zone["id"], dns_data, dns["id"])
        else:
            raise salt.exceptions.ArgumentValueError(
                f"Cloudflare zone not found for {hostname}"
            )
    else:
        raise salt.exceptions.ArgumentValueError(
            f"Not a valid type {type} - must be one of {RECORD_TYPES}"
        )
    
    return _simple_dns(dns)


def remove_dns(hostname):
    """
    Delete a cloudflare dns entry

    hostname
        DNS record to remove

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_dns.remove_dns sub.domain.com

    Returns ``True`` if successful
    """
    api_token = __salt__["config.get"]("cloudflare").get("api_token")
    dns = get_dns(hostname)

    if dns:
        ret_dns = cf_tunnel_utils.remove_dns(api_token, dns["zone_id"], dns["id"])
        if ret_dns:
            return True
        else:
            raise salt.exceptions.CommandExecutionError("Issue removing DNS entry")
    else:
        raise salt.exceptions.ArgumentValueError(f"Could not find DNS entry for {hostname}")
