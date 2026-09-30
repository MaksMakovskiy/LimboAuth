"""Check the standalone SQL fixture; does not run the Java plugin."""

import csv
from pathlib import Path
import sqlite3
import tempfile


directory = Path(__file__).resolve().parent
with (directory / "accounts.tsv").open() as source:
    accounts = list(csv.DictReader(source, delimiter="\t"))

with tempfile.TemporaryDirectory(prefix="limboauth-sql-test-") as temporary:
    database = Path(temporary) / "auth.db"
    with sqlite3.connect(database) as connection:
        connection.executescript((directory / "accounts.sql").read_text())

    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM AUTH").fetchone()[0] == 10
        assert len(accounts) == 10
        for account in accounts:
            stored = connection.execute(
                "SELECT HASH FROM AUTH WHERE LOWERCASENICKNAME = ?",
                (account["nickname"].lower(),),
            ).fetchone()[0]
            assert stored == account["password"]
        try:
            connection.execute(
                "INSERT INTO AUTH (NICKNAME, LOWERCASENICKNAME, HASH) VALUES (?, ?, ?)",
                (accounts[0]["nickname"].upper(), accounts[0]["nickname"].lower(), "other"),
            )
        except sqlite3.IntegrityError:
            connection.rollback()
        else:
            raise AssertionError("Duplicate nickname was accepted")
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

print("PASS: SQL import, 10 persisted plaintext passwords, nickname uniqueness, integrity")
