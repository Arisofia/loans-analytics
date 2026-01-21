import os
from dotenv import load_dotenv
from psycopg import connect

load_dotenv()


class DBManager:
    """Simple DB manager for tests and utilities.

    - Reads DATABASE_URL from env
    - Provides fast TRUNCATE-based cleanup and deterministic seed data
    """

    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL is not set in environment variables")

    def get_connection(self):
        return connect(self.db_url)

    def wipe_database(self):
        """Truncate common tables used by tests.

        Modify `tables_to_clear` to match your schema.
        """
        print("🧹 [Python] Cleaning database (TRUNCATE ... CASCADE)...")
        tables_to_clear = ["public.loans", "public.kpis", "public.notifications"]

        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                for table in tables_to_clear:
                    cur.execute(f"TRUNCATE TABLE {table} CASCADE;")
            conn.commit()
            print("✅ [Python] Tables truncated.")
        except Exception as e:
            print(f"❌ [Python] Error cleaning DB: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def seed_kpi_data(self):
        """Insert deterministic KPI rows used by backend tests and Figma sync validation."""
        print("🌱 [Python] Seeding KPI data...")
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.kpis (label, value, trend, status)
                    VALUES
                    ('Total Loan Volume', '$5,400,000', 12.5, 'positive'),
                    ('Active Borrowers', '142', 5.2, 'neutral'),
                    ('Risk Score', '85/100', -2.1, 'negative');
                    """
                )
            conn.commit()
            print("✅ [Python] KPI data seeded.")
        except Exception as e:
            print(f"❌ [Python] Error seeding KPI data: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()