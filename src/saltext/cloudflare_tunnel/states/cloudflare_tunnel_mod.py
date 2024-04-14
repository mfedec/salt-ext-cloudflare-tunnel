"""
Cloudflare Tunnel State Module

This module is used to manage Cloudflare Zero Trust Tunnels

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

log = logging.getLogger(__name__)

__virtualname__ = "cloudflare_tunnel"


def __virtual__():
    if "cloudflare_tunnel.get_tunnel" not in __salt__:
        return False, "The 'cloudflare_tunnel' execution module is not available"
    return __virtualname__


def present(name, ingress):
    """
    Ensure the tunnel is present

    The following parameters are required:

    name
        This is the name of the Cloudflare Tunnel to create

    ingress
        These are the rules to add, can specify multiple

        It will also add a default catch-all rule

        See `docs <https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
        install-and-setup/tunnel-guide/local/local-management/configuration-file>`_ for config details

    CLI Example:

    .. code-block:: yaml

        cloudflare_tunnel.present:
            - name: test_cf_tunnel
            - ingress:
                - hostname: name.domain.com
                  service: https://127.0.0.1:8000
                  path: test-past
                  originRequest:
                    httpHostheader: something
                - hostname: another.domain.com
                  service: http://127.0.0.1:8080
    """
    ret = {"name": name, "changes": {}, "result": None, "comment": ""}

    tunnel = __salt__["cloudflare_tunnel.get_tunnel"](name)

    create_tunnel = True
    create_dns = []
    remove_dns = []
    update_config = False
    config_service = True
    config_changes = {"old": [], "new": []}

    if tunnel:
        if tunnel["name"] == name:
            create_tunnel = False

        config = __salt__["cloudflare_tunnel.get_tunnel_config"](tunnel["id"])

        if config:
            for rule in ingress:
                if rule not in config["config"]["ingress"]:
                    update_config = True
                    config_changes["new"].append(
                        {"hostname": rule["hostname"], "service": rule["service"]}
                    )

            # Check if there any existing rules that need to be removed
            for rule in config["config"]["ingress"]:
                if rule not in ingress:
                    config_changes["old"].append(
                        {"hostname": rule["hostname"], "service": rule["service"]}
                    )
                    update_config = True

                if "hostname" in rule:
                    if not any(rule["hostname"] in d.values() for d in ingress):
                        dns = __salt__["cloudflare_dns.get_dns"](rule["hostname"])
                        if dns:
                            remove_dns.append(dns["name"])
        else:
            update_config = True
            config_changes["new"] = ingress
    else:
        update_config = True
        config_changes["new"] = ingress

    for rule in ingress:
        if "hostname" in rule:
            dns = __salt__["cloudflare_dns.get_dns"](rule["hostname"])

            if not dns:
                create_dns.append(rule["hostname"])

    if __salt__["cloudflare_tunnel.is_connector_installed"]():
        config_service = False

    if not (create_tunnel or create_dns or update_config or config_service or remove_dns):
        ret["result"] = True
        ret["comment"] = f"Cloudflare Tunnel {name} is already in the desired state"

        return ret

    if create_tunnel:
        if __opts__["test"]:
            ret["comment"] = f"Tunnel {name} will be created"
            return ret

        tunnel = __salt__["cloudflare_tunnel.create_tunnel"](name)

        ret["changes"].setdefault("tunnel created", name)
        ret["result"] = True
        ret["comment"] = f"Cloudflare tunnel {name} was created"

    if update_config:
        if __opts__["test"]:
            ret["comment"] = "Tunnel config will be created/updated"
            return ret

        __salt__["cloudflare_tunnel.create_tunnel_config"](tunnel["id"], {"ingress": ingress})

        ret["changes"].setdefault("tunnel config", config_changes)
        ret["result"] = True

    if create_dns:
        if __opts__["test"]:
            for dns in create_dns:
                ret["comment"] = "\n".join([ret["comment"], f"DNS {dns} will be created"])
            return ret

        for dns in create_dns:
            dns = __salt__["cloudflare_dns.create_dns"](dns, f"{tunnel['id']}.cfargotunnel.com", comment="DNS Managed by SaltStack")

            ret["changes"][dns["name"]] = {
                "content": dns["content"],
                "type": dns["type"],
                "proxied": dns["proxied"],
                "comment": dns["comment"],
                "result": "Added",
            }
            ret["result"] = True

    if remove_dns:
        if __opts__["test"]:
            for dns in remove_dns:
                ret["comment"] = "\n".join([ret["comment"], f"DNS {dns} will be removed"])
            return ret

        for hostname in remove_dns:
            __salt__["cloudflare_dns.remove_dns"](hostname)

            ret["changes"][hostname] = {
                "result": "Removed",
            }
            ret["result"] = True

    if config_service:
        if __opts__["test"]:
            ret["comment"] = "Cloudflare connector will be installed"
            return ret

        if tunnel:
            __salt__["cloudflare_tunnel.install_connector"](tunnel["id"])

            ret["changes"].setdefault("connector installed and started", True)
            ret["result"] = True
        else:
            ret["result"] = False
            ret["comment"] = "Tunnel not found, could not configure the connector"
            return ret

    return ret


def absent(name):
    """
    Ensure tunnel is absent

    name
        This is the name of the Cloudflare Tunnel to delete

    CLI Example:

    .. code-block:: yaml

        cloudflare_tunnel.absent:
            - name: test_cf_tunnel
    """
    ret = {"name": name, "changes": {}, "result": None, "comment": ""}

    tunnel = __salt__["cloudflare_tunnel.get_tunnel"](name)

    if tunnel:
        tunnel_name = tunnel["name"]
        if __opts__["test"]:
            ret["comment"] = f"Cloudflare Tunnel {tunnel_name} will be deleted"
            return ret

        # Check to see if there is a tunnel config, which will contain a hostname that we will
        # need to delete from DNS
        tunnel_config = __salt__["cloudflare_tunnel.get_tunnel_config"](tunnel["id"])

        if tunnel_config:
            __salt__["cloudflare_tunnel.remove_connector"]()
            ret["changes"].setdefault("connector", "removed")
            ret["result"] = True

            dns_changes = []
            for rule in tunnel_config["config"]["ingress"]:
                if "hostname" in rule:
                    hostname = rule["hostname"]

                    dns = __salt__["cloudflare_dns.get_dns"](hostname)
                    if dns:
                        dns_name = dns["name"]
                        __salt__["cloudflare_dns.remove_dns"](dns["name"])
                        dns_changes.append(f"{dns_name} removed")
                        ret["result"] = True

            ret["changes"]["dns"] = dns_changes

        __salt__["cloudflare_tunnel.remove_tunnel"](tunnel["id"])
        ret["comment"] = f"Cloudflare Tunnel {tunnel_name} has been removed"
        ret["changes"].setdefault("tunnel", f"removed {tunnel_name}")
        ret["result"] = True
    else:
        ret["comment"] = f"Cloudflare Tunnel {name} does not exist"
        ret["result"] = True

    return ret
