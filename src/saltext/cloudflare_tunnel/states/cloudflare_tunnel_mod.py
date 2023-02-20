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
    .. code-block: yaml
        ensure cloudflare tunnel is present

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

    The following parameters are required:

    name
        This is the name of the Cloudflare Tunnel to create

    ingress
        These are the rules to add, can specify multiple

        It will also add a default catch-all rule

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
                if (rule not in config["config"]["ingress"]):
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

        if tunnel:
            ret["changes"].setdefault("tunnel created", name)
            ret["result"] = True
            ret["comment"] = f"Cloudflare tunnel {name} was created"
        else:
            ret["result"] = False
            ret["comment"] = f"Failed to create the {name} tunnel"
            return ret

    if create_config:
        if __opts__["test"]:
            ret["comment"] = f"Tunnel config will be created"
            return ret

        tunnel_config = __salt__["cloudflare_tunnel.create_tunnel_config"](
            tunnel["id"], {"ingress": ingress}
        )

        if tunnel_config:
            ret["changes"].setdefault("tunnel config created", "config")

            ret["result"] = True
            ret["comment"] = "\n".join(
                [ret["comment"], f"Tunnel config was created"]
            )
        else:
            ret["result"] = False
            ret["comment"] = "\n".join(
                [ret["comment"], f"Failed to create tunnel config"]
            )
            return ret

    if create_dns:
        for dns in create_dns:
            if __opts__["test"]:
                ret["comment"] = "\n".join(
                    [ret["comment"], f"DNS {dns} will be created"]
                )
                return ret

            dns = __salt__["cloudflare_tunnel.create_dns"](dns, tunnel["id"])

            if dns:
                ret["changes"][dns["name"]] = {"content": dns["content"], "type": dns["type"], "proxied": dns["proxied"], "comment": dns["comment"]}

                ret["result"] = True
                ret["comment"] = "\n".join([ret["comment"], f"DNS entry {dns} was created"])
            else:
                ret["result"] = False
                ret["comment"] = "\n".join(
                    [ret["comment"], f"Failed to create {dns} DNS entry"]
                )

        return ret

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
                return ret
        else:
            ret["result"] = False
            ret["comment"] = "Tunnel not found, could not configure the connector"
            return ret

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

            dns_changes = []
            for rule in tunnel_config["config"]["ingress"]:
                if "hostname" in rule:
                    hostname = rule["hostname"]

                    dns = __salt__["cloudflare_tunnel.get_dns"](hostname)
                    if dns:
                        dns_name = dns["name"]
                        if __salt__["cloudflare_tunnel.remove_dns"](dns["name"]):
                            ret["comment"] = "\n".join(
                                [ret["comment"], f"DNS entry {dns_name} has been removed"]
                            )
                            # ret["changes"][dns["name"]] = "removed"
                            dns_changes.append(f"{dns_name} removed")
                            ret["result"] = True
                        else:
                            ret["comment"] = f"Failed to remove DNS entry {dns_name}"
                            ret["result"] = False
                            return ret

            ret["changes"]["dns"] = dns_changes

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
