from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import salt.modules.linux_service as service
import saltext.cloudflare_tunnel.modules.cloudflare_tunnel_mod as cloudflare_tunnel_module


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {
            "cloudflare_tunnel.is_connector_installed": cloudflare_tunnel_module.is_connector_installed,
        },
    }
    return {
        cloudflare_tunnel_module: module_globals,
    }


def test_is_service_available():
    with patch.dict(
        cloudflare_tunnel_module.__salt__, {"service.available": MagicMock(return_value=True)}
    ):
        assert cloudflare_tunnel_module.is_connector_installed() == True


def test_is_service_not_available():
    with patch.dict(
        cloudflare_tunnel_module.__salt__, {"service.available": MagicMock(return_value=False)}
    ):
        assert cloudflare_tunnel_module.is_connector_installed() == False
