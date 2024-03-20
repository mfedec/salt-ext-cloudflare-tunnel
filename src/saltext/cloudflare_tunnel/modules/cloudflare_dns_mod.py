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
