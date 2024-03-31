# pylint: disable=unused-import
"""
Module for Setting up CloudFlare Zero Trust Tunnels

:depends:
    CloudFlare python module
        This module requires the python wrapper for the CloudFlare API.
        https://github.com/cloudflare/python-cloudflare

    Cloudflared Tunnel Client
        This module requires that the cloudflared utility to be installed.
        https://github.com/cloudflare/cloudflared


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

__virtualname__ = "cloudflare_tunnel"


def __virtual__():
    # Check to make sure the python wrapper for CloudFlare and the CloudFlare CLI are installed
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


def get_tunnel(tunnel_name):
    """
    Get tunnel details for the supplied name

    tunnel_name
        User friendly name of the tunnel

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.get_tunnel sample-tunnel

    Returns a dictionary containing the tunnel details if successful or ``False`` if tunnel doesn't
    exist
    """
    account = __salt__["config.get"]("cloudflare").get("account")
    api_token = __salt__["config.get"]("cloudflare").get("api_token")

    tunnel = cf_tunnel_utils.get_tunnel(api_token, account, tunnel_name)

    if not tunnel:
        return False

    return _simple_tunnel(tunnel[0])


def create_tunnel(tunnel_name):
    """
    Create a cloudflare configured cloudflare tunnel

    tunnel_name
        User friendly name for the tunnel

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.create_tunnel example_tunnel_name

    Returns a dictionary containing the tunnel details if successful or ``False`` if it already
    exists
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

    tunnel_id
        tunnel uuid to remove

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.remove_tunnel <tunnel uuid>

    Returns ``True`` if tunnel removed
    """
    api_token = __salt__["config.get"]("cloudflare").get("api_token")
    account = __salt__["config.get"]("cloudflare").get("account")

    tunnel = cf_tunnel_utils.remove_tunnel(api_token, account, tunnel_id)
    if tunnel:
        return True
    else:
        raise salt.exceptions.ArgumentValueError(f"Unable to find tunnel with id {tunnel_id}")


def get_tunnel_config(tunnel_id):
    """
    Get a cloudflare tunnel configuration

    tunnel_id
        tunnel uuid to get the config of

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.get_tunnel_config <tunnel uuid>

    Returns a dictionary containing the tunnel configuration details or ``False`` if it does not
    exist
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
    /tunnel-guide/local/local-management/configuration-file/ for config options

    Automatically adds the catch-all rule http_status:404

    tunnel_id
        tunnel uuid to add the config to

    config
        ingress rules for the tunnel

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.create_tunnel_config <tunnel uuid> \
'{ingress : [{hostname": "test", "service": "https://localhost:8000" }]}'

    Returns a dictionary containing the tunnel configuration details
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

    Returns ``True`` if it installed or ``False`` if it is not
    """
    return __salt__["service.available"]("cloudflared")


def install_connector(tunnel_id):
    """
    Install the connector service

    tunnel_id
        tunnel uuid to connect cloudflared to

    CLI Example:

    .. code-block:: bash

        salt '*' cloudflare_tunnel.install_connector <tunnel uuid>

    Returns ``True`` if successful
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

    Returns ``True`` if successful
    """
    # Check to see if connector is installed as a service before removing.
    if __salt__["service.available"]("cloudflared"):
        output = __salt__["cmd.run"]("cloudflared service uninstall")

        if "uninstalled successfully" not in output:
            raise salt.exceptions.CommandExecutionError("Error uninstalling connector")

    return True
