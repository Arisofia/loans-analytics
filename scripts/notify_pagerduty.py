import argparse
import sys

import requests


def trigger_pagerduty_incident(routing_key, message):
    """
    Triggers a PagerDuty incident using the Events API V2.
    """
    url = "https://events.pagerduty.com/v2/enqueue"
    payload = {
        "routing_key": routing_key,
        "event_action": "trigger",
        "payload": {
            "summary": message,
            "source": "GitHub Actions",
            "severity": "critical",
        },
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Successfully triggered PagerDuty incident: {response.json()}")
    except Exception as e:
        print(f"Error triggering PagerDuty incident: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger PagerDuty incident")
    parser.add_argument("--routing-key", required=True, help="PagerDuty routing key")
    parser.add_argument("--message", required=True, help="Incident message")

    args = parser.parse_args()
    trigger_pagerduty_incident(args.routing_key, args.message)
