# pylint: disable=unused-import
"""
Module for Setting up Cloudflare Zero Trust Tunnels

:depends: Cloudflare python module

:configuration: This module can be used by specifying the name of a
    configuration profile in the minion config, minion pillar, or master
    config. The module will use the 'cloudflare' key by default

    For example:

    .. code-block:: yaml

        cloudflare:
            api_token:
            account:

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

__virtualname__ = "cloudflare_tunnel"


def __virtual__():
    """
    Check to make sure cloudflare python installed and cloudflared cli
    """
    if not salt.utils.path.which("cloudflared"):
        return (
            False,
            "The cloudflare execution module cannot be loaded: "
            + "cloudflared cli is not installed",
        )

    if HAS_LIBS:
        return __virtualname__

    return (
        False,
        "The cloudflare execution module cannot be loaded: "
        "Cloudflare Python module is not installed.",
    )


def _simple_tunnel(tunnel):
    """
    Simplify the results returned from the API
    """
    return {
        "status": tunnel["status"],
        "id": tunnel["id"],
        "name": tunnel["name"],
        "account_tag": tunnel["account_tag"],
    }


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


def _simple_config(tunnel_config):
    """
    Simplify the results returned from the API
    """
    return {"tunnel_id": tunnel_config["tunnel_id"], "config": tunnel_config["config"]}


def _get_tunnel_token(tunnel_id):
    """
    Generates a tunnel token to be used when installing the cloudflared connector
    """
    api_token = __salt__["config.get"]("cloudflare").get("api_token")
    account = __salt__["config.get"]("cloudflare").get("account")

    return cf_tunnel_utils.get_tunnel_token(api_token, account, tunnel_id)


def _get_zone_id(domain_name):
    """
    Gets the Zone ID from supplied domain name.

    Zone ID is used in the majority of cloudflare api calls. It is the unique ID
    for each domain that is hosted
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


def get_tunnel(tunnel_name):
    """
    Get tunnel details for the supplied name

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.get_tunnel sample-tunnel
    """
    account = __salt__["config.get"]("cloudflare").get("account")
    api_token = __salt__["config.get"]("cloudflare").get("api_token")

    tunnel = cf_tunnel_utils.get_tunnel(api_token, account, tunnel_name)

    if not tunnel:
        return False

    return _simple_tunnel(tunnel[0])


def create_tunnel(tunnel_name):
    """
    Create a locally configured cloudflare tunnel

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.create_tunnel example_tunnel_name
    """
    account = __salt__["config.get"]("cloudflare").get("account")
    api_token = __salt__["config.get"]("cloudflare").get("api_token")

    tunnel = get_tunnel(tunnel_name)

    if tunnel:
        return (False, f"Tunnel {tunnel_name} already exists")
    else:
        tunnel = cf_tunnel_utils.create_tunnel(api_token, account, tunnel_name)

    return _simple_tunnel(tunnel)


def remove_tunnel(tunnel_id):
    """
    Delete a cloudflare tunnel

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.remove_tunnel <tunnel uuid>
    """
    api_token = __salt__["config.get"]("cloudflare").get("api_token")
    account = __salt__["config.get"]("cloudflare").get("account")

    tunnel = cf_tunnel_utils.remove_tunnel(api_token, account, tunnel_id)
    if tunnel:
        return True
    else:
        raise salt.exceptions.ArgumentValueError(f"Unable to find tunnel with id {tunnel_id}")


def get_dns(dns_name):
    """
    Get DNS details for the supplied dns name

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.get_dns sample.example.com
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


def create_dns(hostname, tunnel_id):
    """
    Create cname record for the tunnel

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.create_dns test tunnel_id
    """
    api_token = __salt__["config.get"]("cloudflare").get("api_token")
    zone = _get_zone_id(hostname)

    if zone:
        # Split the dns name to pull out just the domain name to grab the zone id
        domain_split = hostname.split(".")

        dns = get_dns(hostname)

        dns_data = {
            "name": domain_split[0],
            "type": "CNAME",
            "content": f"{tunnel_id}.cfargotunnel.com",
            "ttl": 1,
            "proxied": True,
            "comment": "DNS managed by SaltStack",
        }

        if dns:
            # If DNS exist, check to see if it is pointing to the correct tunnel
            if dns["content"] != f"{tunnel_id}.cfargotunnel.com":
                dns = cf_tunnel_utils.create_dns(api_token, zone["id"], dns_data, dns["id"])
        else:
            dns = cf_tunnel_utils.create_dns(api_token, zone["id"], dns_data)
    else:
        raise salt.exceptions.ArgumentValueError(
            f"Cloudflare zone not found for hostname {hostname}"
        )

    return _simple_dns(dns)


def remove_dns(hostname):
    """
    Delete a cloudflare dns entry

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.remove_dns sub.domain.com
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


def get_tunnel_config(tunnel_id):
    """
    Get a cloudflare tunnel configuration

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.get_tunnel_config <tunnel uuid>
    """
    api_token = __salt__["config.get"]("cloudflare").get("api_token")
    account = __salt__["config.get"]("cloudflare").get("account")

    tunnel_config = cf_tunnel_utils.get_tunnel_config(api_token, account, tunnel_id)
    if tunnel_config["config"] is None:
        return False

    return _simple_config(tunnel_config)


def create_tunnel_config(tunnel_id, config):
    """
    Create a cloudflare tunnel configuration

    See https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup
    /tunnel-guide/local/local-management/configuration-file/

    for config options

    Automatically adds the catch-all rule http_status:404

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.create_tunnel_config <tunnel uuid> \
            '{ingress : [{hostname": "test", "service": "https://localhost:8000" }]}'
    """
    api_token = __salt__["config.get"]("cloudflare").get("api_token")
    account = __salt__["config.get"]("cloudflare").get("account")

    if {"service": "http_status:404"} not in config["ingress"]:
        config["ingress"].append({"service": "http_status:404"})

    tunnel_config = cf_tunnel_utils.create_tunnel_config(
        api_token, account, tunnel_id, {"config": config}
    )

    if not tunnel_config:
        raise salt.exceptions.CommandExecutionError("There was an issue creating the tunnel config")

    return _simple_config(tunnel_config)


def is_connector_installed():
    """
    Check if connector service installed

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.is_connector_installed
    """
    return __salt__["service.available"]("cloudflared")


def install_connector(tunnel_id):
    """
    Install the connector service

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.install_connector <tunnel uuid>
    """
    token = _get_tunnel_token(tunnel_id)

    output = __salt__["cmd.run"](f"cloudflared service install {token}")

    if "installed successfully" not in output:
        raise salt.exceptions.CommandExecutionError("Error installing connector")

    return True


def remove_connector():
    """
    Remove the connector service

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.remove_connector
    """
    # Check to see if connector is installed as a service before removing.
    if __salt__["service.available"]("cloudflared"):
        output = __salt__["cmd.run"]("cloudflared service uninstall")

        if "uninstalled successfully" not in output:
            raise salt.exceptions.CommandExecutionError("Error uninstalling connector")

    return True
