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
import base64
import logging
import random
import string

import salt.utils

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
            "The cloudflare execution module cannot be loaded: " "cloudflared cli is not installed",
        )

    if HAS_LIBS:
        return __virtualname__

    return (
        False,
        "The cloudflare execution module cannot be loaded: "
        "Cloudflare Python module is not installed.",
    )


def _simple_tunnel(tunnel):
    return {
        "status": tunnel["status"],
        "id": tunnel["id"],
        "name": tunnel["name"],
        "account_tag": tunnel["account_tag"],
    }


def _simple_zone(zone):
    return {"id": zone["id"], "name": zone["name"], "status": zone["status"]}


def _simple_dns(dns):
    return {
        "id": dns["id"],
        "name": dns["name"],
        "type": dns["type"],
        "content": dns["content"],
        "proxied": dns["proxied"],
        "zone_id": dns["zone_id"],
    }


def _simple_config(tunnel_config):
    return {
        "tunnel_id": tunnel_config["tunnel_id"],
        "hostname": tunnel_config["config"]["ingress"][0]["hostname"],
        "service": tunnel_config["config"]["ingress"][0]["service"],
    }


def _generate_secret():
    random_string = "".join(
        random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=35)
    )
    random_string_bytes = random_string.encode("ascii")
    base64_string_bytes = base64.b64encode(random_string_bytes)
    base64_string = base64_string_bytes.decode("ascii")

    return base64_string


# Need to make sure we add try exception everywhere.
def _get_tunnel_token(tunnel_id):
    api_token = __salt__["config.get"]("cloudflare").get("api_token")
    account = __salt__["config.get"]("cloudflare").get("account")

    cf_ = CloudFlare.CloudFlare(token=api_token)

    token = cf_.accounts.cfd_tunnel.token.get(account, tunnel_id)

    return token


def _get_zone_id(domain_name):
    """
    Gets the Zone ID from supplied domain name.

    Zone ID is used in the majority of cloudflare api calls. It is the unique ID
    for each domain that is hosted
    """
    zone_details = None
    # Split the dns name to pull out just the domain name to grab the zone id
    domain_split = domain_name.split(".")
    domain_length = len(domain_split)
    domain = f"{domain_split[domain_length - 2]}.{domain_split[domain_length - 1]}"

    api_token = __salt__["config.get"]("cloudflare").get("api_token")

    cf_ = CloudFlare.CloudFlare(token=api_token)
    zone_details = cf_.zones.get(params={"name": domain})

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
    api_token = __salt__["config.get"]("cloudflare").get("api_token")
    account = __salt__["config.get"]("cloudflare").get("account")

    cf_ = CloudFlare.CloudFlare(token=api_token)
    tunnel = cf_.accounts.cfd_tunnel.get(
        account, params={"name": tunnel_name, "is_deleted": "false"}
    )

    if tunnel:
        tunnel_details = {}
        tunnel_details = _simple_tunnel(tunnel[0])
    else:
        return False

    return tunnel_details


def create_tunnel(tunnel_name):
    """
    Create a locally configured cloudflare tunnel

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.create_tunnel example_tunnel_name
    """

    tunnel = get_tunnel(tunnel_name)

    if not tunnel:
        # Tunnel not created or ever created in the past.
        api_token = __salt__["config.get"]("cloudflare").get("api_token")
        account = __salt__["config.get"]("cloudflare").get("account")

        cf_ = CloudFlare.CloudFlare(token=api_token)
        try:
            tunnel = cf_.accounts.cfd_tunnel.post(
                account,
                data={
                    "name": tunnel_name,
                    "tunnel_secret": _generate_secret(),
                    "config_src": "cloudflare",
                },
            )
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            log.exception(e)
            return False

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

    cf_ = CloudFlare.CloudFlare(token=api_token)
    try:
        tunnel = cf_.accounts.cfd_tunnel.delete(account, tunnel_id)
        if tunnel:
            log.info("Tunnel {} has been removed".format(tunnel["name"]))
            return True
        else:
            log.error(f"There was an issue removing the tunnel with id {tunnel_id}")
            return False

    except CloudFlare.exceptions.CloudFlareAPIError as e:
        log.exception(e)
        return False

    log.error(f"There was an issue removing the tunnel with id {tunnel_id}")
    return False


def get_dns(dns_name):
    """
    Get DNS details for the supplied dns name

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.get_dns sample.example.com
    """
    api_token = __salt__["config.get"]("cloudflare").get("api_token")
    account = __salt__["config.get"]("cloudflare").get("account")

    zone = _get_zone_id(dns_name)

    if zone:
        cf_ = CloudFlare.CloudFlare(token=api_token)

        dns_details = cf_.zones.dns_records.get(zone["id"], params={"name": dns_name})

        if dns_details:
            ret_dns_details = {}
            ret_dns_details = _simple_dns(dns_details[0])
        else:
            return False
    else:
        # Need to figure out how to return things like no zone found
        return False

    return ret_dns_details


def create_dns(hostname, tunnel_id):
    """
    Create cname record for the tunnel

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.create_dns test tunnel_id
    """
    api_token = __salt__["config.get"]("cloudflare").get("api_token")
    account = __salt__["config.get"]("cloudflare").get("account")

    # Get the zone
    zone = _get_zone_id(hostname)

    if zone:
        # Split the dns name to pull out just the domain name to grab the zone id
        domain_split = hostname.split(".")

        cf_ = CloudFlare.CloudFlare(token=api_token)

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
                try:
                    dns = cf_.zones.dns_records.put(zone["id"], dns["id"], data=dns_data)

                except CloudFlare.exceptions.CloudFlareAPIError as e:
                    log.exception(e)
                    return False
        else:
            try:
                dns = cf_.zones.dns_records.post(zone["id"], data=dns_data)
            except CloudFlare.exceptions.CloudFlareAPIError as e:
                log.exception(e)
                return False
    else:
        # Need to figure out how to return things like no zone found
        return (False, f"Cloudflare zone not found for hostname {hostname}")

    return _simple_dns(dns)


def remove_dns(hostname):
    """
    Delete a cloudflare dns entry

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.remove_dns sub.domain.com
    """
    dns = get_dns(hostname)

    if dns:
        api_token = __salt__["config.get"]("cloudflare").get("api_token")

        cf_ = CloudFlare.CloudFlare(token=api_token)
        try:
            ret_dns = cf_.zones.dns_records.delete(dns["zone_id"], dns["id"])
            if ret_dns:
                log.info("DNS Entryu {} has been removed".format(dns["name"]))
                return True
            else:
                log.error(f"There was an issue removing the DNS entry {hostname}")
                return False

        except CloudFlare.exceptions.CloudFlareAPIError as e:
            log.exception(e)
            return False
    else:
        log.error("Could not find DNS entry for %s", hostname)
        return False

    log.error("There was an issue removing the DNS entry %s", hostname)
    return False


def get_tunnel_config(tunnel_id):
    """
    Get a cloudflare tunnel configuration

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.get_tunnel_config <tunnel uuid>
    """
    api_token = __salt__["config.get"]("cloudflare").get("api_token")
    account = __salt__["config.get"]("cloudflare").get("account")

    cf_ = CloudFlare.CloudFlare(token=api_token)
    try:
        tunnel_config = cf_.accounts.cfd_tunnel.configurations.get(account, tunnel_id)
        if tunnel_config["config"] is None:
            return False

    except CloudFlare.exceptions.CloudFlareAPIError as e:
        log.exception(e)
        return False

    return _simple_config(tunnel_config)


def create_tunnel_config(tunnel_id, hostname, url):
    """
    Create a cloudflare tunnel configuration

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.create_tunnel_config <tunnel uuid> sub.domain.com https://127.0.0.1
    """
    api_token = __salt__["config.get"]("cloudflare").get("api_token")
    account = __salt__["config.get"]("cloudflare").get("account")

    cf_ = CloudFlare.CloudFlare(token=api_token)
    try:
        config_details = {
            "config": {
                "ingress": [
                    {
                        "service": url,
                        "hostname": hostname,
                    },
                    {
                        "service": "http_status:404",
                    },
                ]
            }
        }

        tunnel_config = cf_.accounts.cfd_tunnel.configurations.put(
            account, tunnel_id, data=config_details
        )
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        log.exception(e)
        return False

    return _simple_config(tunnel_config)


# Don't think I need, using service.available is better for this purpose.
# def is_connector_running():
#     return __salt__["service.status"]("cloudflared")


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
        return False

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
            return False

    return True
