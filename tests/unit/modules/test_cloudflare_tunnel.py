from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import salt.exceptions
import saltext.cloudflare_tunnel.modules.cloudflare_tunnel_mod as cloudflare_tunnel_module


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {
            "config.get": MagicMock(
                return_value={
                    "api_token": "AS0KLASDOK1201KASD1KJ1239ASKJD123",
                    "account": "AS1AELASDOK1201KASD1KJ1239ASADD12",
                }
            )
        },
    }
    return {
        cloudflare_tunnel_module: module_globals,
    }


# IS THIS HOW TO PROPERLY USE FIXTURE?
# Need to learn more about how to use these
@pytest.fixture
def mock_get_zone_id():
    with patch(
        "saltext.cloudflare_tunnel.modules.cloudflare_tunnel_mod._get_zone_id",
        MagicMock(return_value={"id": "1234ABC", "name": "example.com", "status": "active"}),
    ):
        yield


# NEED TO TEST THE EXCEPTION I THINK as well.


# Just pull the mock_dns return value directly from cloudflare API docs.
def test_get_dns_returns_dns(mock_get_zone_id):  # pylint: disable=unused-argument
    mock_dns = [
        {
            "id": "372e67954025e0ba6aaa6d586b9e0b59",
            "type": "A",
            "name": "test.example.com",
            "content": "198.51.100.4",
            "proxiable": True,
            "proxied": False,
            "comment": "Domain verification record",
            "tags": ["owner:dns-team"],
            "ttl": 3600,
            "locked": False,
            "zone_id": "023e105f4ecef8ad9ca31a8372d0c353",
            "zone_name": "example.com",
            "created_on": "2014-01-01T05:20:00.12345Z",
            "modified_on": "2014-01-01T05:20:00.12345Z",
            "data": {},
            "meta": {"auto_added": True, "source": "primary"},
        }
    ]
    with patch(
        "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.get_dns",
        MagicMock(return_value=mock_dns),
    ):
        assert cloudflare_tunnel_module.get_dns("example.com") == {
            "id": "372e67954025e0ba6aaa6d586b9e0b59",
            "name": "test.example.com",
            "type": "A",
            "content": "198.51.100.4",
            "proxied": False,
            "zone_id": "023e105f4ecef8ad9ca31a8372d0c353",
            "comment": "Domain verification record",
        }


def test_get_dns_no_dns(mock_get_zone_id):  # pylint: disable=unused-argument
    with patch(
        "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.get_dns",
        MagicMock(return_value=False),
    ):
        assert cloudflare_tunnel_module.get_dns("example.com") is False


def test_get_dns_no_zone():
    with patch(
        "saltext.cloudflare_tunnel.modules.cloudflare_tunnel_mod._get_zone_id",
        MagicMock(return_value=False),
    ):
        with pytest.raises(salt.exceptions.ArgumentValueError):
            assert cloudflare_tunnel_module.get_dns("example.com") is False


def test_create_dns_does_not_exist(mock_get_zone_id):  # pylint: disable=unused-argument
    mock_dns = []
    create_dns = {
        "id": "372e67954025e0ba6aaa6d586b9e0b59",
        "type": "CNAME",
        "name": "test.example.com",
        "content": "372e67954025e0ba6aaa6d586b9e0b59.cfargotunnel.com",
        "proxiable": True,
        "proxied": True,
        "comment": "DNS managed by SaltStack",
        "tags": ["owner:dns-team"],
        "ttl": 3600,
        "locked": False,
        "zone_id": "023e105f4ecef8ad9ca31a8372d0c353",
        "zone_name": "example.com",
        "created_on": "2014-01-01T05:20:00.12345Z",
        "modified_on": "2014-01-01T05:20:00.12345Z",
        "data": {},
        "meta": {"auto_added": True, "source": "primary"},
    }
    with patch(
        "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.get_dns",
        MagicMock(return_value=mock_dns),
    ):
        with patch(
            "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.create_dns",
            MagicMock(return_value=create_dns),
        ):
            assert cloudflare_tunnel_module.create_dns(
                "test.example.com", "372e67954025e0ba6aaa6d586b9e0b59"
            ) == {
                "id": "372e67954025e0ba6aaa6d586b9e0b59",
                "name": "test.example.com",
                "type": "CNAME",
                "content": "372e67954025e0ba6aaa6d586b9e0b59.cfargotunnel.com",
                "proxied": True,
                "zone_id": "023e105f4ecef8ad9ca31a8372d0c353",
                "comment": "DNS managed by SaltStack",
            }


def test_get_tunnel_returns_tunnel():
    # Not sure what exactly this patch.dict is doing.. works with or without it..
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
    ret_account_tag = 123456
    ret_id = 12345
    ret_name = "test-1234"
    ret_status = "inactive"

    mock_tunnel = [
        {
            "account_tag": ret_account_tag,
            "id": ret_id,
            "name": ret_name,
            "status": ret_status,
        }
    ]
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
    # Not sure what exactly this patch.dict is doing.. works with or without it..
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
        with patch(
            "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.get_tunnel",
            MagicMock(return_value=[]),
        ):
            assert cloudflare_tunnel_module.get_tunnel("test-1234") is False


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
            with pytest.raises(salt.exceptions.CommandExecutionError):
                assert cloudflare_tunnel_module.install_connector("12345")


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
        with pytest.raises(salt.exceptions.CommandExecutionError):
            assert cloudflare_tunnel_module.remove_connector()
