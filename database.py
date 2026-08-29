import sqlite3


# ---------------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------------

# SQLite database file used to store analyzed customer feedback.
DB_FILE = "feedback.db"


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------

def init_db():
    """
    Create the feedback table if it does not already exist.

    If an older version of the database already exists, add the new
    'reason' and 'suggestion' columns without deleting existing data.
    """

    with sqlite3.connect(DB_FILE) as conn:

        # Create the original table if this is a new database.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review TEXT NOT NULL,
                label TEXT NOT NULL,
                score INTEGER NOT NULL,
                theme TEXT NOT NULL
            )
            """
        )

        # Check which columns currently exist in the database.
        columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(feedback)"
            ).fetchall()
        }

        # Add the 'reason' column if it does not exist.
        if "reason" not in columns:
            conn.execute(
                """
                ALTER TABLE feedback
                ADD COLUMN reason TEXT NOT NULL DEFAULT ''
                """
            )

        # Add the 'suggestion' column if it does not exist.
        if "suggestion" not in columns:
            conn.execute(
                """
                ALTER TABLE feedback
                ADD COLUMN suggestion TEXT NOT NULL DEFAULT ''
                """
            )


# ---------------------------------------------------------------------------
# Save analysis results
# ---------------------------------------------------------------------------

def save_results(results):
    """
    Save analyzed customer reviews to the SQLite database.
    """

    with sqlite3.connect(DB_FILE) as conn:

        conn.executemany(
            """
            INSERT INTO feedback (
                review,
                label,
                score,
                theme,
                reason,
                suggestion
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    result["review"],
                    result["label"],
                    result["score"],
                    result["theme"],
                    result["reason"],
                    result["suggestion"],
                )
                for result in results
            ],
        )


# ---------------------------------------------------------------------------
# Load saved history
# ---------------------------------------------------------------------------

def load_history():
    """
    Load all previously saved customer feedback from the database.
    """

    with sqlite3.connect(DB_FILE) as conn:

        return conn.execute(
            """
            SELECT
                review,
                label,
                score,
                theme,
                reason,
                suggestion
            FROM feedback
            ORDER BY id DESC
            """
        ).fetchall()
