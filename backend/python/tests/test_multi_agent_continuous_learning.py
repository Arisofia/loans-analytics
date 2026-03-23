import unittest
from unittest.mock import MagicMock, patch
from backend.python.multi_agent.orchestrator import MultiAgentOrchestrator
from backend.python.multi_agent.protocol import AgentResponse, AgentRole, Message, MessageRole

class TestContinuousLearningLoop(unittest.TestCase):

    @patch('backend.python.multi_agent.base_agent.BaseAgent._init_client')
    def setUp(self, mock_init_client):
        mock_init_client.return_value = MagicMock()
        self.usage_tracker = MagicMock()
        self.orchestrator = MultiAgentOrchestrator(usage_tracker=self.usage_tracker)

    @staticmethod
    def _response(role: AgentRole, trace_id: str, content: str) -> AgentResponse:
        return AgentResponse(trace_id=trace_id, agent_role=role, message=Message(role=MessageRole.ASSISTANT, content=content), tokens_used=150, cost_usd=0.002, latency_ms=35.0)

    def test_run_agent_rejects_empty_commentary(self):
        role = AgentRole.RISK_ANALYST
        self.orchestrator.agents[role].process = MagicMock(return_value=self._response(role=role, trace_id='trace_empty', content='   '))
        with self.assertRaises(ValueError):
            self.orchestrator.run_agent(role=role, messages=[Message(role=MessageRole.USER, content='Analyze risk')], trace_id='trace_empty')

    def test_run_agent_tracks_learning_event(self):
        role = AgentRole.COMPLIANCE
        self.orchestrator.agents[role].process = MagicMock(return_value=self._response(role=role, trace_id='trace_ok', content='Compliance review complete. No material issues found.'))
        response = self.orchestrator.run_agent(role=role, messages=[Message(role=MessageRole.USER, content='Review compliance')], trace_id='trace_ok')
        self.assertTrue(response.metadata.get('commentary_validated'))
        self.assertTrue(any((call.kwargs.get('feature_name') == 'agent_response' and call.kwargs.get('action') == role.value for call in self.usage_tracker.track.call_args_list)))

    def test_run_scenario_collects_agent_comments(self):

        def make_process(role: AgentRole):

            def _process(request):
                return self._response(role=role, trace_id=request.trace_id, content=f'{role.value} commentary generated.')
            return _process
        self.orchestrator.agents[AgentRole.RISK_ANALYST].process = MagicMock(side_effect=make_process(AgentRole.RISK_ANALYST))
        self.orchestrator.agents[AgentRole.COMPLIANCE].process = MagicMock(side_effect=make_process(AgentRole.COMPLIANCE))
        self.orchestrator.agents[AgentRole.OPS_OPTIMIZER].process = MagicMock(side_effect=make_process(AgentRole.OPS_OPTIMIZER))
        results = self.orchestrator.run_scenario('loan_risk_review', initial_context={'portfolio_data': 'sample portfolio'}, trace_id='trace_scenario')
        self.assertIn('_agent_comments', results)
        self.assertEqual(len(results['_agent_comments']), 3)
        self.assertTrue(all((c.get('comment') for c in results['_agent_comments'])))
        self.assertTrue(any((call.kwargs.get('feature_name') == 'scenario_execution' and call.kwargs.get('action') == 'loan_risk_review' for call in self.usage_tracker.track.call_args_list)))

    def test_feedback_updates_learning_summary(self):
        self.orchestrator.record_feedback(trace_id='trace_feedback_1', rating=5, comments='Strong risk rationale and actionable recommendations.', agent_role=AgentRole.RISK_ANALYST)
        self.orchestrator.record_feedback(trace_id='trace_feedback_2', rating=3, comments='Needs clearer next-step prioritization.', agent_role=AgentRole.RISK_ANALYST)
        summary = self.orchestrator.get_learning_summary()
        self.assertEqual(summary['feedback_events'], 2)
        self.assertEqual(summary['average_rating'], 4.0)
        self.assertEqual(summary['by_agent']['risk_analyst']['count'], 2)
        self.assertEqual(summary['by_agent']['risk_analyst']['average_rating'], 4.0)
        self.assertTrue(any((call.kwargs.get('feature_name') == 'agent_feedback' and call.kwargs.get('action') == 'feedback_received' for call in self.usage_tracker.track.call_args_list)))
if __name__ == '__main__':
    unittest.main()
