from unittest.mock import MagicMock
from unittest.mock import patch


import pytest
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


@pytest.fixture
def fake_cloudflare_auth():
    with patch("Cloudflare.Cloudflare"):
        return ["Cloudflare", "REDACTED"]


def test_install_connector():
    with patch.object(cloudflare_tunnel_module, "_get_tunnel_token", MagicMock(return_value="12345")):
        with patch.dict(cloudflare_tunnel_module.__salt__, {"cmd.run": MagicMock(return_value="installed successfully")}):
            assert cloudflare_tunnel_module.install_connector('12345') is True


def test_install_connector_failed():
    with patch.object(cloudflare_tunnel_module, "_get_tunnel_token", MagicMock(return_value="12345")):
        with patch.dict(cloudflare_tunnel_module.__salt__, {"cmd.run": MagicMock(return_value="provided token is invalid")}):
            assert cloudflare_tunnel_module.install_connector('12345') is False


def test_is_service_available():
    with patch.dict(
        cloudflare_tunnel_module.__salt__, {"service.available": MagicMock(return_value=True)}
    ):
        assert cloudflare_tunnel_module.is_connector_installed() is True


def test_is_service_not_available():
    with patch.dict(
        cloudflare_tunnel_module.__salt__, {"service.available": MagicMock(return_value=False)}
    ):
        assert cloudflare_tunnel_module.is_connector_installed() is False


def test_remove_connector_if_not_available():
    with patch.dict(
        cloudflare_tunnel_module.__salt__, {"service.available": MagicMock(return_value=False)}
    ):
        assert cloudflare_tunnel_module.remove_connector() is True


def test_remove_connector_if_available():
    with patch.dict(
        cloudflare_tunnel_module.__salt__,
        {
            "service.available": MagicMock(return_value=True),
            "cmd.run": MagicMock(return_value="uninstalled successfully"),
        },
    ):
        assert cloudflare_tunnel_module.remove_connector() is True


def test_remove_connector_failed():
    with patch.dict(
        cloudflare_tunnel_module.__salt__,
        {
            "service.available": MagicMock(return_value=True),
            "cmd.run": MagicMock(
                return_value="Failed to disable unit: Unit file cloudflared.service does not exist."
            ),
        },
    ):
        assert cloudflare_tunnel_module.remove_connector() is False
