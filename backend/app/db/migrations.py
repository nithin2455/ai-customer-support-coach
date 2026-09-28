"""
Database migration helper for SQLite and SQLAlchemy.
Ensures new schema columns exist in existing database files without data loss.
"""
import logging
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger("db_migrations")


def run_startup_migrations(engine: Engine):
    """
    Checks database tables and idempotently adds missing columns required for
    multilingual support if they do not already exist.
    """
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        # 1. Update conversations table
        if "conversations" in table_names:
            conv_cols = [c["name"] for c in inspector.get_columns("conversations")]
            with engine.connect() as conn:
                if "language_code" not in conv_cols:
                    logger.info("Migrating conversations table: adding language_code column")
                    conn.execute(text("ALTER TABLE conversations ADD COLUMN language_code VARCHAR DEFAULT 'en'"))
                if "locale" not in conv_cols:
                    logger.info("Migrating conversations table: adding locale column")
                    conn.execute(text("ALTER TABLE conversations ADD COLUMN locale VARCHAR DEFAULT 'en-IN'"))
                conn.commit()

        # 2. Update messages table
        if "messages" in table_names:
            msg_cols = [c["name"] for c in inspector.get_columns("messages")]
            with engine.connect() as conn:
                if "language_code" not in msg_cols:
                    logger.info("Migrating messages table: adding language_code column")
                    conn.execute(text("ALTER TABLE messages ADD COLUMN language_code VARCHAR DEFAULT 'en'"))
                if "original_content" not in msg_cols:
                    logger.info("Migrating messages table: adding original_content column")
                    conn.execute(text("ALTER TABLE messages ADD COLUMN original_content TEXT"))
                if "translated_content" not in msg_cols:
                    logger.info("Migrating messages table: adding translated_content column")
                    conn.execute(text("ALTER TABLE messages ADD COLUMN translated_content TEXT"))
                conn.commit()

        logger.info("Database startup migrations verified successfully.")
    except Exception as e:
        logger.warning(f"Startup migration check skipped or failed non-critically: {e}")
