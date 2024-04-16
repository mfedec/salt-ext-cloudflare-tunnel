from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import salt.exceptions
import saltext.cloudflare_tunnel.modules.cloudflare_dns_mod as cloudflare_dns_module


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
        cloudflare_dns_module: module_globals,
    }


# IS THIS HOW TO PROPERLY USE FIXTURE?
# Need to learn more about how to use these
@pytest.fixture
def mock_get_zone_id():
    with patch(
        "saltext.cloudflare_tunnel.utils.cloudflare_mod.get_zone_id",
        MagicMock(return_value=[{"id": "1234ABC", "name": "example.com", "status": "active"}]),
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
        "saltext.cloudflare_tunnel.utils.cloudflare_dns_mod.get_dns",
        MagicMock(return_value=mock_dns),
    ):
        with patch(
            "saltext.cloudflare_tunnel.utils.cloudflare_dns_mod.remove_dns",
            MagicMock(return_value=mock_remove),
        ):
            with pytest.raises(
                salt.exceptions.CommandExecutionError, match="Issue removing DNS entry"
            ):
                assert cloudflare_dns_module.remove_dns("test.example.com")


def test_remove_dns_does_not_exist(mock_get_zone_id):  # pylint: disable=unused-argument
    with patch(
        "saltext.cloudflare_tunnel.utils.cloudflare_dns_mod.get_dns",
        MagicMock(return_value=[]),
    ):
        with pytest.raises(
            salt.exceptions.ArgumentValueError,
            match="Could not find DNS entry for test.example.com",
        ):
            cloudflare_dns_module.remove_dns("test.example.com")


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
        "saltext.cloudflare_tunnel.utils.cloudflare_dns_mod.get_dns",
        MagicMock(return_value=mock_dns),
    ):
        with patch(
            "saltext.cloudflare_tunnel.utils.cloudflare_dns_mod.remove_dns",
            MagicMock(return_value=mock_remove),
        ):
            assert cloudflare_dns_module.remove_dns("test.example.com") is True


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
        "saltext.cloudflare_tunnel.utils.cloudflare_dns_mod.get_dns", MagicMock(return_value=[])
    ):
        with patch(
            "saltext.cloudflare_tunnel.utils.cloudflare_dns_mod.create_dns",
            MagicMock(return_value=mock_dns),
        ):
            assert (
                cloudflare_dns_module.create_dns("example.com", "A", "198.51.100.4")
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
        "saltext.cloudflare_tunnel.utils.cloudflare_dns_mod.get_dns",
        MagicMock(return_value=mock_dns),
    ):
        with patch(
            "saltext.cloudflare_tunnel.utils.cloudflare_dns_mod.create_dns",
            MagicMock(return_value=mock_dns[0]),
        ):
            assert (
                cloudflare_dns_module.create_dns("example.com", "A", "198.51.100.4")
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
        "saltext.cloudflare_tunnel.utils.cloudflare_dns_mod.get_dns",
        MagicMock(return_value=mock_dns),
    ):
        assert cloudflare_dns_module.get_dns("example.com") == expected_result


def test_get_dns_no_dns(mock_get_zone_id):  # pylint: disable=unused-argument
    with patch(
        "saltext.cloudflare_tunnel.utils.cloudflare_dns_mod.get_dns",
        MagicMock(return_value=False),
    ):
        assert cloudflare_dns_module.get_dns("example.com") is False


def test_get_dns_no_zone():
    with patch(
        "saltext.cloudflare_tunnel.modules.cloudflare_dns_mod._get_zone_id",
        MagicMock(return_value=False),
    ):
        with pytest.raises(salt.exceptions.ArgumentValueError):
            assert cloudflare_dns_module.get_dns("example.com") is False
