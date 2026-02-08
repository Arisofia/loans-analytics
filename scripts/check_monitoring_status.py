import asyncio

from python.config import settings
from python.supabase_pool import get_pool


async def check_monitoring():
    try:
        pool = await get_pool(settings.database_url)
        print("Connected to database.")

        print("\n--- Recent Monitoring Events ---")
        # Check if table exists
        table_check_result = await pool.fetch("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE  table_schema = 'monitoring'
                AND    table_name   = 'operational_events'
            );
        """)
        table_check = table_check_result[0][0] if table_check_result else False
        if not table_check:
            print("Table monitoring.operational_events does not exist.")
        else:
            events = await pool.fetch(
                "SELECT * FROM monitoring.operational_events ORDER BY created_at DESC LIMIT 5"
            )
            for event in events:
                src = event["source"]
                sev = event["severity"]
                print(f"[{event['created_at']}] {src}" f" - {sev}: {event['event_type']}")

        print("\n--- Recent Monitoring Commands ---")
        cmd_table_check_result = await pool.fetch("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE  table_schema = 'monitoring'
                AND    table_name   = 'commands'
            );
        """)
        cmd_table_check = cmd_table_check_result[0][0] if cmd_table_check_result else False
        if not cmd_table_check:
            print("Table monitoring.commands does not exist.")
        else:
            commands = await pool.fetch(
                "SELECT * FROM monitoring.commands ORDER BY created_at DESC LIMIT 5"
            )
            for cmd in commands:
                ctype = cmd["command_type"]
                print(f"[{cmd['created_at']}] {ctype}" f" - {cmd['status']}: {cmd['requested_by']}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(check_monitoring())
