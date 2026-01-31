#!/usr/bin/env python3
"""
Quick Supabase connection test script.

Tests connection to Supabase database and validates environment setup.
Run this before load testing to ensure credentials are correct.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.supabase_pool import SupabaseConnectionPool


async def test_connection():
    """Test Supabase database connection."""
    print("=" * 80)
    print("SUPABASE CONNECTION TEST")
    print("=" * 80)

    # Get database URL
    database_url = os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL")

    if not database_url:
        print("\n❌ ERROR: No database URL found")
        print("\nPlease set one of these environment variables:")
        print(
            "  export SUPABASE_DATABASE_URL='postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres'"
        )
        print(
            "  export DATABASE_URL='postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres'"
        )
        return False

    # Mask password in output
    masked_url = database_url
    if "@" in masked_url:
        prefix, rest = masked_url.split("@", 1)
        if ":" in prefix:
            protocol, user_pass = prefix.rsplit("://", 1)
            if ":" in user_pass:
                user, _ = user_pass.split(":", 1)
                masked_url = f"{protocol}://{user}:***@{rest}"

    print("\n📋 Configuration:")
    print(f"  URL: {masked_url}")

    # Test connection
    try:
        print("\n🔌 Testing connection...")
        pool = SupabaseConnectionPool(database_url, min_size=1, max_size=2)

        await pool.initialize()
        print("  ✅ Connection pool initialized")

        # Test query
        result = await pool.fetchval("SELECT 1 as test")
        print(f"  ✅ Test query successful: {result}")

        # Check fact_loans table
        try:
            count = await pool.fetchval("SELECT COUNT(*) FROM fact_loans")
            print(f"  ✅ fact_loans table exists: {count:,} rows")
        except Exception as e:
            print(f"  ⚠️  fact_loans table check failed: {e}")
            print("     (Table may not exist - this is OK for testing)")

        # Get pool metrics
        metrics = pool.get_metrics()
        print("\n📊 Pool Metrics:")
        print(f"  Total connections: {metrics['total_connections']}")
        print(f"  Active connections: {metrics['active_connections']}")
        print(f"  Queries executed: {metrics['queries_executed']}")

        await pool.close()
        print("\n✅ Connection test PASSED - ready for load testing!")
        return True

    except Exception as e:
        print(f"\n❌ Connection test FAILED: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify your Supabase project is active")
        print("  2. Check your database password is correct")
        print("  3. Ensure your IP is whitelisted in Supabase settings")
        print("  4. Try using the connection pooler URL instead:")
        print(
            "     postgresql://postgres.[PROJECT]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres"
        )
        return False


def main():
    """Run connection test."""
    try:
        success = asyncio.run(test_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
