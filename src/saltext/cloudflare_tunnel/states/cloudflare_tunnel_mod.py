"""
Salt state module
"""
import logging

log = logging.getLogger(__name__)

__virtualname__ = "cloudflare_tunnel"


def __virtual__():
    # To force a module not to load return something like:
    #   return (False, "The cloudflare_tunnel state module is not implemented yet")

    # Replace this with your own logic
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
    create_config = False
    config_service = True

    if tunnel:
        if tunnel["name"] == name:
            create_tunnel = False

        config = __salt__["cloudflare_tunnel.get_tunnel_config"](tunnel["id"])

        if config:
            for rule in ingress:
                if rule not in config["config"]["ingress"]:
                    create_config = True
        else:
            create_config = True
    else:
        create_config = True

    for rule in ingress:
        if "hostname" in rule:
            dns = __salt__["cloudflare_tunnel.get_dns"](rule["hostname"])

            if dns and tunnel:
                if (
                    dns["name"] != rule["hostname"]
                    and dns["content"] != f"{tunnel['id']}.cfargotunnel.com"
                    and dns["proxied"]
                ):
                    create_dns.append(dns["name"])
            else:
                create_dns.append(rule["hostname"])

    if __salt__["cloudflare_tunnel.is_connector_installed"]():
        config_service = False

    if not (create_tunnel or create_dns or create_config or config_service):
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

    if create_config:
        if __opts__["test"]:
            ret["comment"] = "Tunnel config will be created"
            return ret

        __salt__["cloudflare_tunnel.create_tunnel_config"](tunnel["id"], {"ingress": ingress})

        ret["changes"].setdefault("tunnel config", "created/updated")
        ret["result"] = True

    if create_dns:
        if __opts__["test"]:
            for dns in create_dns:
                ret["comment"] = "\n".join([ret["comment"], f"DNS {dns} will be created"])
            return ret

        for dns in create_dns:
            dns = __salt__["cloudflare_tunnel.create_dns"](dns, tunnel["id"])

            ret["changes"][dns["name"]] = {
                "content": dns["content"],
                "type": dns["type"],
                "proxied": dns["proxied"],
                "comment": dns["comment"],
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

                    dns = __salt__["cloudflare_tunnel.get_dns"](hostname)
                    if dns:
                        dns_name = dns["name"]
                        __salt__["cloudflare_tunnel.remove_dns"](dns["name"])
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
