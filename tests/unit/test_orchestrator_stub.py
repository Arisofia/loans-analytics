

from orchestration.orchestrator import Orchestrator, WorkflowDefinition, AgentTask, TaskPriority, WorkflowStatus


class DummyAgent:
    def execute(self, objective, context):
        return {"success": True, "output": f"done: {objective}", "status": "completed"}


def test_orchestrator_workflow_execution():
    orchestrator = Orchestrator(max_workers=2)
    agent = DummyAgent()
    orchestrator.register_agent("dummy", agent)

    # Create two tasks, one depends on the other
    task1 = AgentTask(
        id="t1",
        agent_name="dummy",
        objective="step 1",
        priority=TaskPriority.HIGH,
        timeout=10,
        dependencies=[],
        status=WorkflowStatus.PENDING,
        start_time=None,
        end_time=None,
    )
    task2 = AgentTask(
        id="t2",
        agent_name="dummy",
        objective="step 2",
        priority=TaskPriority.MEDIUM,
        timeout=10,
        dependencies=["t1"],
        status=WorkflowStatus.PENDING,
        start_time=None,
        end_time=None,
    )
    workflow = WorkflowDefinition(
        id="wf1",
        name="Test Workflow",
        description="A test workflow",
        tasks=[task1, task2],
        max_parallel=2,
        timeout=60,
    )
    orchestrator.create_workflow(workflow)
    result = orchestrator.execute_workflow("wf1")
    assert result["success"] is True
    assert result["workflow_id"] == "wf1"
    assert result["execution_record"]["completed_tasks"] == 2
    assert result["execution_record"]["failed_tasks"] == 0
    orchestrator.shutdown()
