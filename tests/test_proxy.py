import pytest
from engine.proxy import ProxyManager

@pytest.mark.asyncio
async def test_proxy_creation():
    pm = ProxyManager()
    assert pm is not None
    assert len(pm.proxies) > 0
