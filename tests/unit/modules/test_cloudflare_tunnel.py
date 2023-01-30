import pytest
import salt.modules.test as testmod
import saltext.cloudflare_tunnel.modules.cloudflare_tunnel_mod as cloudflare_tunnel_module


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {"test.echo": testmod.echo},
    }
    return {
        cloudflare_tunnel_module: module_globals,
    }
