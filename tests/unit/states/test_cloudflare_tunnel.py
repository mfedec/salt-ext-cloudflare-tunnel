from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.cloudflare_tunnel.modules.cloudflare_tunnel_mod as cloudflare_tunnel_module
import saltext.cloudflare_tunnel.states.cloudflare_tunnel_mod as cloudflare_tunnel_state


@pytest.fixture
def configure_loader_modules():
    return {
        cloudflare_tunnel_module: {
            "__salt__": {
            },
        },
        cloudflare_tunnel_state: {
            "__salt__": {
                # "cloudflare_tunnel.example_function": cloudflare_tunnel_module.example_function,
            },
        },
    }


def test_absent_no_changes():
    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {},
        "result": True,
        "comment": "Cloudflare Tunnel cf_tunnel_example does not exist"
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value={})
        }
    ):
        assert cloudflare_tunnel_state.absent("cf_tunnel_example") == expected_result


def test_absent_changes_test_mode():
    mock_tunnel = {
        "status": "healthy",
        "id": "f70ff985-a4ef-4643-bbbc-4a0ed4fc8415",
        "name": "cf_tunnel_example",
        "account_tag": "699d98642c564d2e855e9661899b7252"
    }

    expected_result = {
        "name": "cf_tunnel_example",
        "changes": {},
        "result": None,
        "comment": "Cloudflare Tunnel cf_tunnel_example will be deleted"
    }

    with patch.dict(
        cloudflare_tunnel_state.__salt__,
        {
            "cloudflare_tunnel.get_tunnel": MagicMock(return_value=mock_tunnel)
        }
    ):
        with patch.dict(
            cloudflare_tunnel_state.__opts__, { "test": True }
        ):
            assert cloudflare_tunnel_state.absent("cf_tunnel_example") == expected_result
