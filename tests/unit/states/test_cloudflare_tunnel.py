from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.cloudflare_tunnel.modules.cloudflare_tunnel_mod as cloudflare_tunnel_module
import saltext.cloudflare_tunnel.modules.cloudflare_dns_mod as cloudflare_dns_module
import saltext.cloudflare_tunnel.states.cloudflare_tunnel_mod as cloudflare_tunnel_state


mock_tunnel = {
    "status": "healthy",
    "id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
    "name": "cf_tunnel_example",
    "account_tag": "699d98642c564d2e855e9661899b7252",
}

mock_config = {
    "tunnel_id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
    "config": {
        "warp-routing": {"enabled": True},
        "originRequest": {"connectTimeout": 10},
        "ingress": [
            {"hostname": "test.example.com", "service": "https://localhost:8000"},
            {"service": "http_status:404"},
        ],
    },
}

mock_dns = {
    "id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
    "name": "test.example.com",
    "type": "CNAME",
    "content": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415.cfargotunnel.com",
    "proxied": True,
    "zone_id": "023e105f4ecef8ad9ca31a8372d0c353",
    "comment": "Managed by SaltStack",
}

mock_config_multiple = {
    "tunnel_id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
    "config": {
        "warp-routing": {"enabled": True},
        "originRequest": {"connectTimeout": 10},
        "ingress": [
            {"hostname": "test.example.com", "service": "https://localhost:8000"},
            {"hostname": "test-2.example.com", "service": "https://localhost:443"},
            {"hostname": "test-3.example.com", "service": "https://localhost:7474"},
            {"service": "http_status:404"},
        ],
    },
}

mock_dns_multiple = [
    {
        "id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
        "name": "test.example.com",
        "type": "CNAME",
        "content": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415.cfargotunnel.com",
        "proxied": True,
        "zone_id": "023e105f4ecef8ad9ca31a8372d0c353",
        "comment": "Managed by SaltStack",
    },
    {
        "id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
        "name": "test-2.example.com",
        "type": "CNAME",
        "content": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415.cfargotunnel.com",
        "proxied": True,
        "zone_id": "023e105f4ecef8ad9ca31a8372d0c353",
        "comment": "Managed by SaltStack",
    },
    {
        "id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
        "name": "test-3.example.com",
        "type": "CNAME",
        "content": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415.cfargotunnel.com",
        "proxied": True,
        "zone_id": "023e105f4ecef8ad9ca31a8372d0c353",
        "comment": "Managed by SaltStack",
    },
]

ingress_rules = [
    {"hostname": "test.example.com", "service": "https://localhost:8000"},
    {"service": "http_status:404"},
]

ingress_rules_multiple = [
    {"hostname": "test.example.com", "service": "https://localhost:8000"},
    {"hostname": "test-2.example.com", "service": "https://localhost:443"},
    {"hostname": "test-3.example.com", "service": "https://localhost:7474"},
    {"service": "http_status:404"},
]


@pytest.fixture
def configure_loader_modules():
    return {
        cloudflare_tunnel_module: {
            "__salt__": {},
        },
        cloudflare_tunnel_state: {
            "__salt__": {
                # "cloudflare_tunnel.example_function": cloudflare_tunnel_module.example_function,
            },
        }
    }


def test_present():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {
            "tunnel created": "cf_tunnel_example",
            "tunnel config": "created/updated",
            "test.example.com": {
                "comment": "Managed by SaltStack",
                "content": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415.cfargotunnel.com",
                "proxied": True,
                "type": "CNAME",
                "result": "Added",
            },
            "connector installed and started": True,
        },
        "result": True,
        "comment": "Cloudflare tunnel cf_tunnel_example was created",
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value=False),
            "cloudflare_tunnel.get_tunnel_config": MagicMock(return_value=False),
            "cloudflare_dns.get_dns": MagicMock(return_value=False),
            "cloudflare_tunnel.is_connector_installed": MagicMock(return_value=False),
            "cloudflare_tunnel.create_tunnel": MagicMock(return_value=mock_tunnel),
            "cloudflare_tunnel.create_tunnel_config": MagicMock(return_value=mock_config),
            "cloudflare_dns.create_dns": MagicMock(return_value=mock_dns),
            "cloudflare_tunnel.install_connector": MagicMock(return_value=True),
        },
    ):
        with patch.dict(cloudflare_tunnel_state.__opts__, {"test": False}):
            assert (
                cloudflare_tunnel_state.present("cf_tunnel_example", ingress_rules)
                == expected_result
            )


def test_present_multiple_dns():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {
            "tunnel created": "cf_tunnel_example",
            "tunnel config": "created/updated",
            "test.example.com": {
                "comment": "Managed by SaltStack",
                "content": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415.cfargotunnel.com",
                "proxied": True,
                "type": "CNAME",
                "result": "Added",
            },
            "test-2.example.com": {
                "comment": "Managed by SaltStack",
                "content": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415.cfargotunnel.com",
                "proxied": True,
                "type": "CNAME",
                "result": "Added",
            },
            "test-3.example.com": {
                "comment": "Managed by SaltStack",
                "content": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415.cfargotunnel.com",
                "proxied": True,
                "type": "CNAME",
                "result": "Added",
            },
            "connector installed and started": True,
        },
        "result": True,
        "comment": "Cloudflare tunnel cf_tunnel_example was created",
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value=False),
            "cloudflare_tunnel.get_tunnel_config": MagicMock(return_value=False),
            "cloudflare_dns.get_dns": MagicMock(return_value=False),
            "cloudflare_tunnel.is_connector_installed": MagicMock(return_value=False),
            "cloudflare_tunnel.create_tunnel": MagicMock(return_value=mock_tunnel),
            "cloudflare_tunnel.create_tunnel_config": MagicMock(return_value=mock_config_multiple),
            "cloudflare_dns.create_dns": MagicMock(side_effect=mock_dns_multiple),
            "cloudflare_tunnel.install_connector": MagicMock(return_value=True),
        },
    ):
        with patch.dict(cloudflare_tunnel_state.__opts__, {"test": False}):
            assert (
                cloudflare_tunnel_state.present("cf_tunnel_example", ingress_rules_multiple)
                == expected_result
            )


def test_present_update_ingress_dns():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {
            "tunnel config": "created/updated",
            "test-4.example.com": {
                "content": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415.cfargotunnel.com",
                "type": "CNAME",
                "proxied": True,
                "comment": "Managed by SaltStack",
                "result": "Added",
            },
            "test.example.com": {
                "result": "Removed",
            },
        },
        "result": True,
        "comment": "",
    }

    updated_ingress_rules = [
        {"hostname": "test-4.example.com", "service": "https://localhost:8000"},
        {"service": "http_status:404"},
    ]

    updated_mock_config = {
        "tunnel_id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
        "config": {
            "warp-routing": {"enabled": True},
            "originRequest": {"connectTimeout": 10},
            "ingress": [
                {"hostname": "test-4.example.com", "service": "https://localhost:8000"},
                {"service": "http_status:404"},
            ],
        },
    }

    updated_mock_dns = {
        "id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
        "name": "test-4.example.com",
        "type": "CNAME",
        "content": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415.cfargotunnel.com",
        "proxied": True,
        "zone_id": "023e105f4ecef8ad9ca31a8372d0c353",
        "comment": "Managed by SaltStack",
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value=mock_tunnel),
            "cloudflare_tunnel.get_tunnel_config": MagicMock(return_value=mock_config),
            "cloudflare_dns.get_dns": MagicMock(side_effect=[mock_dns, False, mock_dns]),
            "cloudflare_tunnel.is_connector_installed": MagicMock(return_value=True),
            "cloudflare_tunnel.create_tunnel_config": MagicMock(return_value=updated_mock_config),
            "cloudflare_dns.create_dns": MagicMock(return_value=updated_mock_dns),
            "cloudflare_dns.remove_dns": MagicMock(return_value=True),
        },
    ):
        with patch.dict(cloudflare_tunnel_state.__opts__, {"test": False}):
            assert (
                cloudflare_tunnel_state.present("cf_tunnel_example", updated_ingress_rules)
                == expected_result
            )


def test_present_remove_ingress_rule():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {
            "tunnel config": "created/updated",
            "test.example.com": {
                "result": "Removed",
            },
        },
        "result": True,
        "comment": "",
    }

    updated_mock_config = {
        "tunnel_id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
        "config": {
            "warp-routing": {"enabled": True},
            "originRequest": {"connectTimeout": 10},
            "ingress": [
                {"service": "http_status:404"},
            ],
        },
    }

    updated_ingress_rules = [
        {"service": "http_status:404"},
    ]

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value=mock_tunnel),
            "cloudflare_tunnel.get_tunnel_config": MagicMock(return_value=mock_config),
            "cloudflare_dns.get_dns": MagicMock(return_value=mock_dns),
            "cloudflare_tunnel.is_connector_installed": MagicMock(return_value=True),
            "cloudflare_tunnel.create_tunnel_config": MagicMock(return_value=updated_mock_config),
            "cloudflare_dns.remove_dns": MagicMock(return_value=True),
        },
    ):
        with patch.dict(cloudflare_tunnel_state.__opts__, {"test": False}):
            assert (
                cloudflare_tunnel_state.present("cf_tunnel_example", updated_ingress_rules)
                == expected_result
            )


def test_present_update_ingress_rule():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {
            "tunnel config": "created/updated",
        },
        "result": True,
        "comment": "",
    }

    updated_mock_config = {
        "tunnel_id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
        "config": {
            "warp-routing": {"enabled": True},
            "originRequest": {"connectTimeout": 10},
            "ingress": [
                {"hostname": "test.example.com", "service": "https://localhost:8080"},
                {"service": "http_status:404"},
            ],
        },
    }

    updated_ingress_rules = [
        {"hostname": "test.example.com", "service": "https://localhost:8080"},
        {"service": "http_status:404"},
    ]

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value=mock_tunnel),
            "cloudflare_tunnel.get_tunnel_config": MagicMock(return_value=mock_config),
            "cloudflare_dns.get_dns": MagicMock(return_value=mock_dns),
            "cloudflare_tunnel.is_connector_installed": MagicMock(return_value=True),
            "cloudflare_tunnel.create_tunnel_config": MagicMock(return_value=updated_mock_config),
        },
    ):
        with patch.dict(cloudflare_tunnel_state.__opts__, {"test": False}):
            assert (
                cloudflare_tunnel_state.present("cf_tunnel_example", updated_ingress_rules)
                == expected_result
            )


def test_present_no_changes():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {},
        "result": True,
        "comment": "Cloudflare Tunnel cf_tunnel_example is already in the desired state",
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value=mock_tunnel),
            "cloudflare_tunnel.get_tunnel_config": MagicMock(return_value=mock_config),
            "cloudflare_dns.get_dns": MagicMock(return_value=mock_dns),
            "cloudflare_tunnel.is_connector_installed": MagicMock(return_value=True),
        },
    ):
        with patch.dict(cloudflare_tunnel_state.__opts__, {"test": False}):
            assert (
                cloudflare_tunnel_state.present("cf_tunnel_example", ingress_rules)
                == expected_result
            )


def test_present_create_tunnel_test_mode():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {},
        "result": None,
        "comment": "Tunnel cf_tunnel_example will be created",
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value=False),
            "cloudflare_tunnel.get_tunnel_config": MagicMock(return_value=False),
            "cloudflare_dns.get_dns": MagicMock(return_value=False),
            "cloudflare_tunnel.is_connector_installed": MagicMock(return_value=False),
        },
    ):
        with patch.dict(cloudflare_tunnel_state.__opts__, {"test": True}):
            assert (
                cloudflare_tunnel_state.present("cf_tunnel_example", ingress_rules)
                == expected_result
            )


def test_present_create_config_test_mode():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {},
        "result": None,
        "comment": "Tunnel config will be created/updated",
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value=mock_tunnel),
            "cloudflare_tunnel.get_tunnel_config": MagicMock(return_value=False),
            "cloudflare_dns.get_dns": MagicMock(return_value=False),
            "cloudflare_tunnel.is_connector_installed": MagicMock(return_value=False),
        },
    ):
        with patch.dict(cloudflare_tunnel_state.__opts__, {"test": True}):
            assert (
                cloudflare_tunnel_state.present("cf_tunnel_example", ingress_rules)
                == expected_result
            )


def test_present_create_dns_test_mode():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {},
        "result": None,
        "comment": "\nDNS test.example.com will be created",
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value=mock_tunnel),
            "cloudflare_tunnel.get_tunnel_config": MagicMock(return_value=mock_config),
            "cloudflare_dns.get_dns": MagicMock(return_value=False),
            "cloudflare_tunnel.is_connector_installed": MagicMock(return_value=False),
        },
    ):
        with patch.dict(cloudflare_tunnel_state.__opts__, {"test": True}):
            assert (
                cloudflare_tunnel_state.present("cf_tunnel_example", ingress_rules)
                == expected_result
            )


def test_present_create_dns_multiple_test_mode():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {},
        "result": None,
        "comment": "\nDNS test.example.com will be created\nDNS test-2.example.com will be created\
\nDNS test-3.example.com will be created",
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value=mock_tunnel),
            "cloudflare_tunnel.get_tunnel_config": MagicMock(return_value=mock_config_multiple),
            "cloudflare_dns.get_dns": MagicMock(return_value=False),
            "cloudflare_tunnel.is_connector_installed": MagicMock(return_value=False),
        },
    ):
        with patch.dict(cloudflare_tunnel_state.__opts__, {"test": True}):
            assert (
                cloudflare_tunnel_state.present("cf_tunnel_example", ingress_rules_multiple)
                == expected_result
            )


def test_present_install_connector_test_mode():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {},
        "result": None,
        "comment": "Cloudflare connector will be installed",
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value=mock_tunnel),
            "cloudflare_tunnel.get_tunnel_config": MagicMock(return_value=mock_config),
            "cloudflare_dns.get_dns": MagicMock(return_value=mock_dns),
            "cloudflare_tunnel.is_connector_installed": MagicMock(return_value=False),
        },
    ):
        with patch.dict(cloudflare_tunnel_state.__opts__, {"test": True}):
            assert (
                cloudflare_tunnel_state.present("cf_tunnel_example", ingress_rules)
                == expected_result
            )


def test_absent():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {
            "connector": "removed",
            "dns": ["test.example.com removed"],
            "tunnel": "removed cf_tunnel_example",
        },
        "result": True,
        "comment": "Cloudflare Tunnel cf_tunnel_example has been removed",
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value=mock_tunnel),
            "cloudflare_tunnel.get_tunnel_config": MagicMock(return_value=mock_config),
            "cloudflare_tunnel.remove_connector": MagicMock(return_value=True),
            "cloudflare_dns.get_dns": MagicMock(return_value=mock_dns),
            "cloudflare_tunnel.remove_tunnel": MagicMock(return_value=True),
            "cloudflare_dns.remove_dns": MagicMock(return_value=True),
        },
    ):
        with patch.dict(cloudflare_tunnel_state.__opts__, {"test": False}):
            assert cloudflare_tunnel_state.absent("cf_tunnel_example") == expected_result


def test_absent_multiple_dns():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {
            "connector": "removed",
            "dns": [
                "test.example.com removed",
                "test-2.example.com removed",
                "test-3.example.com removed",
            ],
            "tunnel": "removed cf_tunnel_example",
        },
        "result": True,
        "comment": "Cloudflare Tunnel cf_tunnel_example has been removed",
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value=mock_tunnel),
            "cloudflare_tunnel.get_tunnel_config": MagicMock(return_value=mock_config_multiple),
            "cloudflare_tunnel.remove_connector": MagicMock(return_value=True),
            "cloudflare_dns.get_dns": MagicMock(side_effect=mock_dns_multiple),
            "cloudflare_tunnel.remove_tunnel": MagicMock(return_value=True),
            "cloudflare_dns.remove_dns": MagicMock(return_value=True),
        },
    ):
        with patch.dict(cloudflare_tunnel_state.__opts__, {"test": False}):
            assert cloudflare_tunnel_state.absent("cf_tunnel_example") == expected_result


def test_absent_no_changes():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {},
        "result": True,
        "comment": "Cloudflare Tunnel cf_tunnel_example does not exist",
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {"cloudflare_tunnel.get_tunnel": MagicMock(return_value={})},
    ):
        assert cloudflare_tunnel_state.absent("cf_tunnel_example") == expected_result


def test_absent_changes_test_mode():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {},
        "result": None,
        "comment": "Cloudflare Tunnel cf_tunnel_example will be deleted",
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {"cloudflare_tunnel.get_tunnel": MagicMock(return_value=mock_tunnel)},
    ):
        with patch.dict(cloudflare_tunnel_state.__opts__, {"test": True}):
            assert cloudflare_tunnel_state.absent("cf_tunnel_example") == expected_result


def test_absent_tunnel_does_not_exist():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {},
        "result": True,
        "comment": "Cloudflare Tunnel cf_tunnel_example does not exist",
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {"cloudflare_tunnel.get_tunnel": MagicMock(return_value=False)},
    ):
        assert cloudflare_tunnel_state.absent("cf_tunnel_example") == expected_result
