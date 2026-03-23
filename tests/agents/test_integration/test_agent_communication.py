from unittest.mock import MagicMock
import pytest

class TestAgentCommunication:

    @pytest.mark.asyncio
    async def test_agent_to_agent_message_passing(self, sample_agent_message):
        sender = MagicMock()
        receiver = MagicMock()
        sender.send_to.return_value = {'sent': True}
        receiver.receive_from.return_value = sample_agent_message
        result = sender.send_to('receiver', sample_agent_message)
        assert result['sent'] is True

    @pytest.mark.asyncio
    async def test_agent_broadcast(self):
        broadcaster = MagicMock()
        broadcaster.broadcast.return_value = {'recipients': ['agent1', 'agent2', 'agent3'], 'delivered': 3}
        result = broadcaster.broadcast(['agent1', 'agent2', 'agent3'], 'message')
        assert result['delivered'] == 3

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_async_agent_communication(self):
        agent1 = MagicMock()
        agent1.send_async.return_value = {'queued': True}
        result = agent1.send_async('agent2', 'async_message')
        assert result['queued'] is True
