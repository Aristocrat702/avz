import pytest
from engine.attack import AsyncAttackEngine

@pytest.mark.asyncio
async def test_engine_creation():
    engine = AsyncAttackEngine()
    assert engine is not None
