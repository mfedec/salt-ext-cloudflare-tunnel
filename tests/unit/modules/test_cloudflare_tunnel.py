from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.cloudflare_tunnel.modules.cloudflare_tunnel_mod as cloudflare_tunnel_module


@pytest.fixture
def configure_loader_modules():
    return {cloudflare_tunnel_module: {}}
    # module_globals = {
    #     "__salt__": {
    #         "cloudflare_tunnel.is_connector_installed": cloudflare_tunnel_module.is_connector_installed,
    #     },

    # }
    # return {
    #     cloudflare_tunnel_module: module_globals,
    # }


## NEED TO TEST THE EXCEPTION I THINK as well.


def test_get_tunnel_returns_tunnel():
    ## Not sure what exactly this patch.dict is doing.. works with or without it..
    # with patch.dict(
    #     cloudflare_tunnel_module.__pillar__,
    #     {
    #         "cloudflare": {
    #             "api_token": "SOMEASDKJA2123ASD",
    #             "account": "aLKAJSDJKLADLJKA",
    #             "tunnel": {
    #                 "hostname": "test.example.com",
    #                 "password": "http://127.0.0.1:8080",
    #             }
    #         }
    #     },
    # ):
    dunder_salt = {
        "config.get": MagicMock(return_value={}),
    }
    with patch.dict(cloudflare_tunnel_module.__salt__, dunder_salt):
        ret_account_tag = 123456
        ret_id = 12345
        ret_name = "test-1234"
        ret_status = "inactive"

        mock_tunnel = {
            "account_tag": ret_account_tag,
            "id": ret_id,
            "name": ret_name,
            "status": ret_status,
        }
        with patch(
            "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.get_tunnel",
            MagicMock(return_value=mock_tunnel),
        ):
            assert cloudflare_tunnel_module.get_tunnel("test-1234") == {
                "account_tag": ret_account_tag,
                "id": ret_id,
                "name": ret_name,
                "status": ret_status,
            }


def test_get_tunnel_returns_nothing():
    ## Not sure what exactly this patch.dict is doing.. works with or without it..
    with patch.dict(
        cloudflare_tunnel_module.__pillar__,
        {
            "cloudflare": {
                "api_token": "SOMEASDKJA2123ASD",
                "account": "aLKAJSDJKLADLJKA",
                "tunnel": {
                    "hostname": "test.example.com",
                    "password": "http://127.0.0.1:8080",
                },
            }
        },
    ):
        with patch.dict(
            cloudflare_tunnel_module.__salt__, {"config.get": MagicMock(return_value={})}
        ):

            with patch(
                "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.get_tunnel",
                MagicMock(return_value=[]),
            ):
                assert cloudflare_tunnel_module.get_tunnel("test-1234") == False


def test_install_connector():
    with patch.object(
        cloudflare_tunnel_module, "_get_tunnel_token", MagicMock(return_value="12345")
    ):
        with patch.dict(
            cloudflare_tunnel_module.__salt__,
            {"cmd.run": MagicMock(return_value="installed successfully")},
        ):
            assert cloudflare_tunnel_module.install_connector("12345") is True


def test_install_connector_failed():
    with patch.object(
        cloudflare_tunnel_module, "_get_tunnel_token", MagicMock(return_value="12345")
    ):
        with patch.dict(
            cloudflare_tunnel_module.__salt__,
            {"cmd.run": MagicMock(return_value="provided token is invalid")},
        ):
            assert cloudflare_tunnel_module.install_connector("12345") is False


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
