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


def test_remove_dns_error_returned(mock_get_zone_id):  # pylint: disable=unused-argument
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

    mock_remove = False

    with patch(
        "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.get_dns",
        MagicMock(return_value=mock_dns),
    ):
        with patch(
            "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.remove_dns",
            MagicMock(return_value=mock_remove),
        ):
            with pytest.raises(
                salt.exceptions.CommandExecutionError, match="Issue removing DNS entry"
            ):
                assert cloudflare_tunnel_module.remove_dns("test.example.com")


def test_remove_dns_does_not_exist(mock_get_zone_id):  # pylint: disable=unused-argument
    mock_dns = []

    with patch(
        "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.get_dns",
        MagicMock(return_value=mock_dns),
    ):
        with pytest.raises(
            salt.exceptions.ArgumentValueError,
            match="Could not find DNS entry for test.example.com",
        ):
            assert cloudflare_tunnel_module.remove_dns("test.example.com")


def test_remove_dns(mock_get_zone_id):  # pylint: disable=unused-argument
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

    mock_remove = {"id": "372e67954025e0ba6aaa6d586b9e0b59"}

    with patch(
        "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.get_dns",
        MagicMock(return_value=mock_dns),
    ):
        with patch(
            "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.remove_dns",
            MagicMock(return_value=mock_remove),
        ):
            assert cloudflare_tunnel_module.remove_dns("test.example.com") is True


def test_create_dns_if_does_not_exist(mock_get_zone_id):  # pylint: disable=unused-argument
    mock_dns = {
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

    expected_result = {
        "id": "372e67954025e0ba6aaa6d586b9e0b59",
        "name": "test.example.com",
        "type": "A",
        "content": "198.51.100.4",
        "proxied": False,
        "zone_id": "023e105f4ecef8ad9ca31a8372d0c353",
        "comment": "Domain verification record",
    }

    with patch(
        "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.get_dns", MagicMock(return_value=[])
    ):
        with patch(
            "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.create_dns",
            MagicMock(return_value=mock_dns),
        ):
            assert (
                cloudflare_tunnel_module.create_dns("example.com", "134129123912SADASD91231SAD")
                == expected_result
            )


def test_create_dns_if_exist(mock_get_zone_id):  # pylint: disable=unused-argument
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

    expected_result = {
        "id": "372e67954025e0ba6aaa6d586b9e0b59",
        "name": "test.example.com",
        "type": "A",
        "content": "198.51.100.4",
        "proxied": False,
        "zone_id": "023e105f4ecef8ad9ca31a8372d0c353",
        "comment": "Domain verification record",
    }

    with patch(
        "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.get_dns",
        MagicMock(return_value=mock_dns),
    ):
        with patch(
            "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.create_dns",
            MagicMock(return_value=mock_dns[0]),
        ):
            assert (
                cloudflare_tunnel_module.create_dns("example.com", "134129123912SADASD91231SAD")
                == expected_result
            )


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

    mock_tunnel = [{
        "id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
        "account_tag": "699d98642c564d2e855e9661899b7252",
        "created_at": "2021-01-25T18:22:34.317854Z",
        "deleted_at": "2009-11-10T23:00:00Z",
        "name": "blog",
        "connections": [
            {
                "colo_name": "DFW",
                "uuid": "1bedc50d-42b3-473c-b108-ff3d10c0d925",
                "id": "1bedc50d-42b3-473c-b108-ff3d10c0d925",
                "is_pending_reconnect": False,
                "origin_ip": "85.12.78.6",
                "opened_at": "2021-01-25T18:22:34.317854Z",
                "client_id": "1bedc50d-42b3-473c-b108-ff3d10c0d925",
                "client_version": "2022.7.1"
            }
        ],
        "conns_active_at": "2009-11-10T23:00:00Z",
        "conns_inactive_at": "2009-11-10T23:00:00Z",
        "tun_type": "cfd_tunnel",
        "metadata": {},
        "status": "healthy",
        "remote_config": True
    }]

    expected_result = {
        "status": "healthy",
        "id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
        "name": "blog",
        "account_tag": "699d98642c564d2e855e9661899b7252"
    }

    with patch(
        "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.get_tunnel",
        MagicMock(return_value=mock_tunnel),
    ):
        assert cloudflare_tunnel_module.get_tunnel("test-1234") == expected_result


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


def test_create_tunnel_returns_tunnel():
    mock_tunnel = {
        "id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
        "account_tag": "699d98642c564d2e855e9661899b7252",
        "created_at": "2021-01-25T18:22:34.317854Z",
        "deleted_at": "2009-11-10T23:00:00Z",
        "name": "blog",
        "connections": [
            {
                "colo_name": "DFW",
                "uuid": "1bedc50d-42b3-473c-b108-ff3d10c0d925",
                "id": "1bedc50d-42b3-473c-b108-ff3d10c0d925",
                "is_pending_reconnect": False,
                "origin_ip": "85.12.78.6",
                "opened_at": "2021-01-25T18:22:34.317854Z",
                "client_id": "1bedc50d-42b3-473c-b108-ff3d10c0d925",
                "client_version": "2022.7.1"
            }
        ],
        "conns_active_at": "2009-11-10T23:00:00Z",
        "conns_inactive_at": "2009-11-10T23:00:00Z",
        "tun_type": "cfd_tunnel",
        "metadata": {},
        "status": "healthy",
        "remote_config": True
    }

    expected_result = {
        "status": "healthy",
        "id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
        "name": "blog",
        "account_tag": "699d98642c564d2e855e9661899b7252"
    }

    with patch(
        "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.get_tunnel",
        MagicMock(return_value={})
    ):
        with patch(
            "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.create_tunnel",
            MagicMock(return_value=mock_tunnel)
        ):
            assert cloudflare_tunnel_module.create_tunnel("blog") == expected_result


def test_create_tunnel_already_exists():
    mock_tunnel = [{
        "id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
        "account_tag": "699d98642c564d2e855e9661899b7252",
        "created_at": "2021-01-25T18:22:34.317854Z",
        "deleted_at": "2009-11-10T23:00:00Z",
        "name": "blog",
        "connections": [
            {
                "colo_name": "DFW",
                "uuid": "1bedc50d-42b3-473c-b108-ff3d10c0d925",
                "id": "1bedc50d-42b3-473c-b108-ff3d10c0d925",
                "is_pending_reconnect": False,
                "origin_ip": "85.12.78.6",
                "opened_at": "2021-01-25T18:22:34.317854Z",
                "client_id": "1bedc50d-42b3-473c-b108-ff3d10c0d925",
                "client_version": "2022.7.1"
            }
        ],
        "conns_active_at": "2009-11-10T23:00:00Z",
        "conns_inactive_at": "2009-11-10T23:00:00Z",
        "tun_type": "cfd_tunnel",
        "metadata": {},
        "status": "healthy",
        "remote_config": True
    }]

    expected_result = (False, "Tunnel blog already exists")

    with patch(
        "saltext.cloudflare_tunnel.utils.cloudflare_tunnel_mod.get_tunnel",
        MagicMock(return_value=mock_tunnel)
    ):
        assert cloudflare_tunnel_module.create_tunnel("blog") == expected_result


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
