import pytest
import salt.modules.test as testmod
import saltext.cloudflare_tunnel.modules.cloudflare_tunnel_mod as cloudflare_tunnel_module
import saltext.cloudflare_tunnel.states.cloudflare_tunnel_mod as cloudflare_tunnel_state


@pytest.fixture
def configure_loader_modules():
    return {
        cloudflare_tunnel_module: {
            "__salt__": {
                "test.echo": testmod.echo,
            },
        },
        cloudflare_tunnel_state: {
            "__salt__": {
                "cloudflare_tunnel.example_function": cloudflare_tunnel_module.example_function,
            },
        },
    }
