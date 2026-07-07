import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    db_path = 'krishi_pro.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Define target schema
    tables = {
        "profile": [
            ("id", "INTEGER PRIMARY KEY"),
            ("name", "TEXT"),
            ("mobile", "TEXT UNIQUE"),
            ("state", "TEXT"),
            ("district", "TEXT"),
            ("village", "TEXT"),
            ("crops", "TEXT"),
            ("krishi_score", "INTEGER"),
            ("pin", "TEXT")
        ],
        "chat_history": [
            ("id", "INTEGER PRIMARY KEY"),
            ("session_id", "TEXT"),
            ("role", "TEXT"),
            ("content", "TEXT"),
            ("metadata", "TEXT"),
            ("timestamp", "TEXT")
        ],
        "shared_knowledge": [
            ("id", "INTEGER PRIMARY KEY"),
            ("question", "TEXT UNIQUE"),
            ("answer", "TEXT"),
            ("metadata", "TEXT"),
            ("date", "TEXT")
        ],
        "ledger": [
            ("id", "INTEGER PRIMARY KEY"),
            ("type", "TEXT"),
            ("amount", "REAL"),
            ("note", "TEXT"),
            ("date", "TEXT")
        ],
        "farm_logs": [
            ("id", "INTEGER PRIMARY KEY"),
            ("crop", "TEXT"),
            ("sowing_date", "TEXT"),
            ("area", "TEXT")
        ]
    }

    for table_name, columns in tables.items():
        # Create table if not exists
        cols_def = ", ".join([f"{name} {dtype}" for name, dtype in columns])
        c.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({cols_def})")
        logger.info(f"Verified/Created table: {table_name}")

        # Check for missing columns
        c.execute(f"PRAGMA table_info({table_name})")
        existing_cols = [row[1] for row in c.fetchall()]
        
        for col_name, col_type in columns:
            if col_name not in existing_cols:
                logger.info(f"Adding missing column {col_name} to {table_name}")
                # Note: SQLite ALTER TABLE ADD COLUMN has some limitations but works for simple types
                try:
                    c.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type.replace('PRIMARY KEY', '').replace('UNIQUE', '')}")
                except sqlite3.OperationalError as e:
                    logger.error(f"Error adding column {col_name}: {e}")

    conn.commit()
    conn.close()
    logger.info("Migration successful!")

if __name__ == "__main__":
    migrate()
