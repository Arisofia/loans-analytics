import azure.functions as func
import logging
import os
from datetime import datetime

from agents.hubspot.segment_manager import SegmentManagerAgent
from agents.base_agent import AgentConfig, AgentContext

app = func.FunctionApp()

def _initialize_and_run_agent(trigger_type: str, user_id: str, name_suffix: str) -> dict:
    model_name = os.getenv("AGENT_MODEL", "gpt-4")
    temperature = float(os.getenv("AGENT_TEMPERATURE", 0.3))
    config = AgentConfig(name="HubSpotSegmentManager", description="Creates daily contact segments in HubSpot", model=model_name, temperature=temperature)
    context = AgentContext(user_id=user_id, session_id=f"{trigger_type}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}", metadata={"trigger": trigger_type})
    agent = SegmentManagerAgent(config=config, context=context)
    logging.info(f"Executing tool 'create_today_segment' with suffix: '{name_suffix}'")
    return agent.execute_tool(tool_name="create_today_segment", tool_input={"name_suffix": name_suffix})

@app.schedule(schedule="0 0 8 * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
def hubspot_daily_segment(timer: func.TimerRequest) -> None:
    timestamp = datetime.utcnow().isoformat()
    if timer.past_due:
        logging.warning(f'Timer trigger is running late. Timestamp: {timestamp}')
    logging.info(f'Starting HubSpot daily segment creation at {timestamp}')
    try:
        result = _initialize_and_run_agent(trigger_type="timer", user_id="system", name_suffix="Auto")
        if result.get("success"):
            logging.info(f"✅ Successfully created segment: {result.get('name')} (ID: {result.get('list_id')})")
            logging.info(f"   URL: {result.get('url')}")
        else:
            error_msg = result.get("error", "Unknown error during segment creation.")
            logging.error(f"❌ Failed to create segment: {error_msg}")
            raise Exception(f"Segment creation failed: {error_msg}")
    except Exception as e:
        logging.exception(f"❌ An unhandled error occurred in hubspot_daily_segment: {e}")
        raise
    logging.info(f"Completed HubSpot daily segment creation at {datetime.utcnow().isoformat()}")

@app.function_name(name="HttpTriggerManualSegment")
@app.route(route="create-segment", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def manual_segment_creation(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('HTTP trigger: Manual HubSpot segment creation requested.')
    try:
        req_body = req.get_json() if req.get_body() else {}
        name_suffix = req_body.get('name_suffix', 'Manual')
    except ValueError:
        name_suffix = 'Manual'
    try:
        result = _initialize_and_run_agent(trigger_type="http", user_id="http-trigger", name_suffix=name_suffix)
        if result.get("success"):
            return func.HttpResponse(body=f"Successfully created segment: {result.get('name')}\nURL: {result.get('url')}", status_code=200, mimetype="text/plain")
        else:
            return func.HttpResponse(body=f"Failed to create segment: {result.get('error')}", status_code=500, mimetype="text/plain")
    except Exception as e:
        logging.exception(f"An unhandled error occurred in manual_segment_creation: {e}")
        return func.HttpResponse(body=f"Internal Server Error: {str(e)}", status_code=500, mimetype="text/plain")
