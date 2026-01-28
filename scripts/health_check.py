#!/usr/bin/env python3
"""Health check script for multi-agent system components.

Checks connectivity and health of Supabase, n8n webhooks, and agent services.
"""

import argparse
import os
import sys
import time
from typing import Dict, Tuple

try:
    import requests
except ImportError:
    print("❌ requests library not found. Install with: pip install requests")
    sys.exit(1)


def check_supabase() -> Tuple[bool, str]:
    """Check Supabase connectivity.

    Returns:
        Tuple of (success, message)
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url:
        return False, "SUPABASE_URL environment variable not set"

    try:
        # Try to access the REST API endpoint
        response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers={"apikey": supabase_key} if supabase_key else {},
            timeout=10,
        )

        if response.status_code in [200, 401, 404]:
            return True, f"Supabase reachable at {supabase_url}"
        else:
            return False, f"Supabase returned status code: {response.status_code}"

    except requests.exceptions.RequestException as e:
        return False, f"Supabase connection failed: {str(e)}"


def check_n8n() -> Tuple[bool, str]:
    """Check n8n webhook endpoint.

    Returns:
        Tuple of (success, message)
    """
    n8n_url = os.getenv("N8N_WEBHOOK_URL")

    if not n8n_url:
        return False, "N8N_WEBHOOK_URL environment variable not set"

    try:
        # Send a health check ping
        response = requests.get(
            n8n_url,
            timeout=10,
        )

        if response.status_code in [200, 404, 405]:
            # 404/405 is acceptable - endpoint exists but needs POST
            return True, f"n8n webhook reachable at {n8n_url}"
        else:
            return False, f"n8n webhook returned status code: {response.status_code}"

    except requests.exceptions.RequestException as e:
        return False, f"n8n webhook connection failed: {str(e)}"


def check_agents() -> Tuple[bool, str]:
    """Check agent system responsiveness.

    Returns:
        Tuple of (success, message)
    """
    # Check if agent modules can be imported
    try:
        import sys
        from pathlib import Path

        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from src.agents.monitoring import CostTracker, PerformanceTracker

        # Try to create instances
        CostTracker()
        PerformanceTracker()

        return True, "Agent monitoring system operational"

    except ImportError as e:
        return False, f"Agent system import failed: {str(e)}"
    except Exception as e:
        return False, f"Agent system check failed: {str(e)}"


def check_llm_provider() -> Tuple[bool, str]:
    """Check LLM provider connectivity.

    Returns:
        Tuple of (success, message)
    """
    openai_key = os.getenv("OPENAI_API_KEY")

    if not openai_key:
        return False, "OPENAI_API_KEY environment variable not set"

    try:
        # Try a simple API call
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {openai_key}"},
            timeout=10,
        )

        if response.status_code == 200:
            return True, "OpenAI API accessible"
        elif response.status_code == 401:
            return False, "OpenAI API key invalid"
        else:
            return False, f"OpenAI API returned status code: {response.status_code}"

    except requests.exceptions.RequestException as e:
        return False, f"OpenAI API connection failed: {str(e)}"


def run_health_checks(checks: list) -> Dict[str, Tuple[bool, str]]:
    """Run specified health checks.

    Args:
        checks: List of check names to run

    Returns:
        Dictionary of check results
    """
    available_checks = {
        "supabase": check_supabase,
        "n8n": check_n8n,
        "agents": check_agents,
        "llm": check_llm_provider,
    }

    results = {}
    for check_name in checks:
        if check_name in available_checks:
            print(f"🔍 Checking {check_name}...")
            success, message = available_checks[check_name]()
            results[check_name] = (success, message)

            if success:
                print(f"  ✅ {message}")
            else:
                print(f"  ❌ {message}")
        else:
            print(f"  ⚠️  Unknown check: {check_name}")

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Health check for multi-agent system")
    parser.add_argument(
        "checks",
        nargs="*",
        default=["supabase", "n8n", "agents"],
        help="Checks to run (supabase, n8n, agents, llm, all)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Overall timeout in seconds",
    )
    args = parser.parse_args()

    # Expand "all" to all checks
    if "all" in args.checks:
        args.checks = ["supabase", "n8n", "agents", "llm"]

    print("🏥 Multi-Agent System Health Check\n")

    start_time = time.time()
    results = run_health_checks(args.checks)
    elapsed = time.time() - start_time

    # Summary
    print("\n" + "=" * 60)
    print(f"⏱️  Health check completed in {elapsed:.2f}s\n")

    all_passed = all(success for success, _ in results.values())
    total = len(results)
    passed = sum(1 for success, _ in results.values() if success)

    print(f"📊 Results: {passed}/{total} checks passed\n")

    if all_passed:
        print("✅ All systems operational")
        sys.exit(0)
    else:
        print("❌ Some systems are not healthy")
        sys.exit(1)


if __name__ == "__main__":
    main()
