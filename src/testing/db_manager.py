import os

from sqlalchemy import create_engine, text


class DBManager:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            # Fallback for when running tests without DB, though fixture skips.
            # But the init shouldn't fail if we just want to instantiate it maybe?
            # The fixture checks env var first.
            pass
        else:
            self.engine = create_engine(self.database_url)

    def wipe_database(self):
        """Wipes all relevant tables."""
        if not hasattr(self, "engine"):
            return

        tables = ["analytics_kpi_metrics", "analytics_timeseries", "analytics_raw_data"]
        with self.engine.connect() as conn:
            for table in tables:
                try:
                    conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
                    conn.commit()
                except Exception:
                    pass

    def seed_kpi_data(self):
        """Seeds initial KPI data."""
        # Placeholder for seeding logic
