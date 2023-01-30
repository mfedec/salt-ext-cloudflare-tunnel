import pytest

pytestmark = [
    pytest.mark.requires_salt_modules("cloudflare_tunnel.example_function"),
]
