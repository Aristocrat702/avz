import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

from botnet.spreader import ssh_bruteforce, quick_port_scan

@patch('botnet.spreader.quick_port_scan', new=AsyncMock(return_value=[22]))
@patch('botnet.spreader.asyncssh.connect', new=AsyncMock(side_effect=Exception))
@pytest.mark.asyncio
async def test_ssh_bruteforce_no_connect():
    success, pwd = await ssh_bruteforce('192.168.1.1')
    assert success == False

@patch('botnet.spreader.quick_port_scan', new=AsyncMock(return_value=[]))
@pytest.mark.asyncio
async def test_quick_port_scan_empty():
    ports = await quick_port_scan('10.0.0.1', [22, 80])
    assert ports == []

@patch('botnet.spreader.socket.socket')
def test_quick_port_scan_success(mock_socket):
    mock_sock_instance = MagicMock()
    mock_sock_instance.connect_ex.return_value = 0
    mock_socket.return_value = mock_sock_instance
    
    async def run():
        return await quick_port_scan('10.0.0.1', [22])
    ports = asyncio.run(run())
    assert 22 in ports
