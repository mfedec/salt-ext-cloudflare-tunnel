
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
        if dns["name"] == hostname and dns["content"] == "{}.cfargotunnel.com".format(tunnel["id"]) and dns["proxied"]:
            create_dns = False

    if __salt__['cloudflare_tunnel.is_connector_installed']():
        config_service = False

    if not (create_tunnel or create_dns or create_config or config_service):
        ret["result"] = True
        ret["comment"] = "Cloudflare Tunnel {} is already in the desired state".format(name)

        return ret

    if create_tunnel:
        if __opts__["test"]:
            ret["comment"] = "Tunnel {} will be created".format(name)
            return ret

        tunnel = __salt__["cloudflare_tunnel.create_tunnel"](name)

        if tunnel:
            ret["changes"].setdefault("tunnel created", name)
            ret["result"] = True
            ret["comment"] = "Cloudflare tunnel {} was created".format(name)
        else:
            ret["result"] = False
            ret["comment"] = "Failed to create the {} tunnel".format(name)

    if create_config:
        if __opts__["test"]:
            ret["comment"] = "Tunnel {} config will be created".format(hostname)
            return ret

        tunnel_config = __salt__["cloudflare_tunnel.create_tunnel_config"](tunnel["id"], hostname, service)

        if tunnel_config:
            ret["changes"].setdefault("tunnel config created", hostname)

            ret["result"] = True
            ret["comment"] = "\n".join([ret["comment"], "Tunnel config for {} was created".format(hostname)])
        else:
            ret["result"] = False
            ret["comment"] = "\n".join([ret["comment"], "Failed to create tunnel config for {}".format(hostname)])

    if create_dns:
        if __opts__["test"]:
            ret["comment"] = "DNS {} will be created".format(hostname)
            return ret

        dns = __salt__["cloudflare_tunnel.create_dns"](hostname, tunnel["id"])

        if dns:
            ret["changes"].setdefault("dns created", dns["name"])

            ret["result"] = True
            ret["comment"] = "\n".join([ret["comment"], "DNS entry {} was created".format(dns["name"])])
        else:
            ret["result"] = False
            ret["comment"] = "\n".join([ret["comment"], "Failed to create {} DNS entry".format(dns["name"])])

    if config_service:
        if __opts__["test"]:
            ret["comment"] = "Cloudflare connector will be installed ".format(hostname)
            return ret

        if tunnel:
            connector = __salt__["cloudflare_tunnel.install_connector"](tunnel["id"])

            if connector:
                ret["changes"].setdefault("connector installed and started", True)
                ret["result"] = True
                ret["comment"] = "\n".join([ret["comment"], "Connector was installed configured for {}".format(tunnel["name"])])
            else:
                ret["result"] = False
                ret["comment"] = "\n".join([ret["comment"], "Failed to configure connector"])
        else:
            ret["result"] = False
            ret["comment"] = "Tunnel not found, could not configure the connector"

    return ret

# cloudflare.present: hmm, if one of the things fails, but the rest don't, result = True, but it would need to
# be false, so it shows failed.. how to best do that? Do we just fail at the first part?

## TODO: How do we update a config? dns? tunnel name?

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
        if __opts__["test"]:
            ret["comment"] = "Cloudflare Tunnel {} will be deleted".format(name)
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
                if __salt__["cloudflare_tunnel.remove_dns"](dns["name"]):
                    ret["comment"] = "\n".join([ret["comment"],"DNS entry {} has been removed".format(dns["name"])])
                    ret["changes"].setdefault("dns", "removed {}".format(dns["name"]))
                    ret["result"] = True
                else:
                    ret["comment"] = "Failed to remove DNS entry{}".format(dns["name"])
                    ret["result"] = False
                    return ret

        if __salt__["cloudflare_tunnel.remove_tunnel"](tunnel["id"]):
            ret["comment"] = "\n".join([ret["comment"],"Cloudflare Tunnel {} has been removed".format(tunnel["name"])])
            ret["changes"].setdefault("tunnel", "removed {}".format(tunnel["name"]))
            ret["result"] = True
        else:
            ret["comment"] = "Failed to remove Cloudflare tunnel {}".format(tunnel["name"])
            ret["result"] = False
            return ret
    else:
        ret["comment"] = "Cloudflare Tunnel {} does not exist".format(name)
        ret["result"] = True

    return ret
