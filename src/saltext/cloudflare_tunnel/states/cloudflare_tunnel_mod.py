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


def present(name, hostname, service):
    """
    .. code-block: yaml
        ensure cloudflare tunnel is present

        cloudflare_tunnel.present:
            - name: test_cf_tunnel
            - hostname: name.domain.com
            - service: https://127.0.0.1:8000

    The following parameters are required:

    name
        This is the name of the Cloudflare Tunnel to create

    """
    ret = {"name": name, "changes": {}, "result": None, "comment": ""}

    tunnel = __salt__["cloudflare_tunnel.get_tunnel"](name)
    dns = __salt__["cloudflare_tunnel.get_dns"](hostname)
    # config = __salt__["cloudflare_tunnel.get_tunnel_config"](tunnel["id"])

    create_tunnel = True
    create_dns = True
    create_config = True
    config_service = True

    if tunnel:
        config = __salt__["cloudflare_tunnel.get_tunnel_config"](tunnel["id"])
        if tunnel["name"] == name:
            create_tunnel = False

        if config:
            if config["hostname"] == hostname and config["service"] == service:
                create_config = False

    if dns and tunnel:
        if (
            dns["name"] == hostname
            # and dns["content"] == "{}.cfargotunnel.com".format(tunnel["id"])
            and dns["content"] == f"{tunnel['id']}.cfargotunnel.com"
            and dns["proxied"]
        ):
            create_dns = False

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

        if tunnel:
            ret["changes"].setdefault("tunnel created", name)
            ret["result"] = True
            ret["comment"] = f"Cloudflare tunnel {name} was created"
        else:
            ret["result"] = False
            ret["comment"] = f"Failed to create the {name} tunnel"

    if create_config:
        if __opts__["test"]:
            ret["comment"] = f"Tunnel {hostname} config will be created"
            return ret

        tunnel_config = __salt__["cloudflare_tunnel.create_tunnel_config"](
            tunnel["id"], hostname, service
        )

        if tunnel_config:
            ret["changes"].setdefault("tunnel config created", hostname)

            ret["result"] = True
            ret["comment"] = "\n".join(
                [ret["comment"], f"Tunnel config for {hostname} was created"]
            )
        else:
            ret["result"] = False
            ret["comment"] = "\n".join(
                [ret["comment"], f"Failed to create tunnel config for {hostname}"]
            )

    if create_dns:
        if __opts__["test"]:
            ret["comment"] = f"DNS {hostname} will be created"
            return ret

        dns = __salt__["cloudflare_tunnel.create_dns"](hostname, tunnel["id"])

        if dns:
            ret["changes"].setdefault("dns created", dns["name"])

            ret["result"] = True
            ret["comment"] = "\n".join([ret["comment"], "DNS entry {dns['name']} was created"])
        else:
            ret["result"] = False
            ret["comment"] = "\n".join([ret["comment"], "Failed to create {dns['name']} DNS entry"])

    if config_service:
        if __opts__["test"]:
            ret["comment"] = "Cloudflare connector will be installed "
            return ret

        if tunnel:
            tunnel_name = tunnel["name"]
            connector = __salt__["cloudflare_tunnel.install_connector"](tunnel["id"])

            if connector:
                ret["changes"].setdefault("connector installed and started", True)
                ret["result"] = True
                ret["comment"] = "\n".join(
                    [
                        ret["comment"],
                        f"Connector was installed configured for {tunnel_name}",
                    ]
                )
            else:
                ret["result"] = False
                ret["comment"] = "\n".join([ret["comment"], "Failed to configure connector"])
        else:
            ret["result"] = False
            ret["comment"] = "Tunnel not found, could not configure the connector"

    return ret


def absent(name):
    """
    .. code-block: yaml
        ensure cloudflare tunnel is absent

        cloudflare_tunnel.absent:
            - name: test_cf_tunnel

    The following parameters are required:

    name
        This is the name of the Cloudflare Tunnel to delete

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
            connector = __salt__["cloudflare_tunnel.remove_connector"]()
            if connector:
                ret["comment"] = "Cloudflare connector has been removed"
                ret["changes"].setdefault("connector", "removed")
                ret["result"] = True
            else:
                ret["comment"] = "Failed to uninstall the cloudflare connector"
                ret["result"] = False
                return ret

            dns = __salt__["cloudflare_tunnel.get_dns"](tunnel_config["hostname"])
            if dns:
                dns_name = dns["name"]
                if __salt__["cloudflare_tunnel.remove_dns"](dns["name"]):
                    ret["comment"] = "\n".join(
                        [ret["comment"], f"DNS entry {dns_name} has been removed"]
                    )
                    ret["changes"].setdefault("dns", f"removed {dns_name}")
                    ret["result"] = True
                else:
                    ret["comment"] = f"Failed to remove DNS entry {dns_name}"
                    ret["result"] = False
                    return ret

        if __salt__["cloudflare_tunnel.remove_tunnel"](tunnel["id"]):
            ret["comment"] = "\n".join(
                [ret["comment"], f"Cloudflare Tunnel {tunnel_name} has been removed"]
            )
            ret["changes"].setdefault("tunnel", f"removed {tunnel_name}")
            ret["result"] = True
        else:
            ret["comment"] = f"Failed to remove Cloudflare tunnel {tunnel_name}"
            ret["result"] = False
            return ret
    else:
        ret["comment"] = f"Cloudflare Tunnel {name} does not exist"
        ret["result"] = True

    return ret
