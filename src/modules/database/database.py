import datetime
import sqlite3

import streamlit as st


class AutoCloseCursur(sqlite3.Cursor):
    # Auto close cursor
    def __init__(self, connection):
        super().__init__(connection)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def dict_factory(cursor, row):
    # Convert sqlite3.Row to dict
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class Database:
    def __init__(self, db_path: str = "resource/database.db"):
        self.db_path = db_path
        with sqlite3.connect(db_path) as conn:
            with AutoCloseCursur(conn) as cur:
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS chat_logs(chat_id, name, role,message, sent_time);"
                )

                cur.execute(
                    "CREATE TABLE IF NOT EXISTS character(chat_id,persona,name PRIMARY KEY);"
                )

                cur.execute("CREATE TABLE IF NOT EXISTS membar(chat_id,time,name);")
            conn.commit()

    def insert_chat_log(
        self, chat_id: str, name: str, role: str, message: str, sent_time: str
    ):
        # Insert chat log into database
        with sqlite3.connect(self.db_path) as conn:
            with AutoCloseCursur(conn) as cur:
                cur.execute(
                    "INSERT INTO chat_logs VALUES (?, ?, ?, ?, ?);",
                    (chat_id, name, role, message, sent_time),
                )
            conn.commit()

    def get_chat_log(self, chat_id: str, limit: int = None):
        # Get chat log from database
        ret_rows = None
        with sqlite3.connect(self.db_path) as conn:
            with AutoCloseCursur(conn) as cur:
                if limit is None:
                    cur.execute(
                        "SELECT chat_id, name, role, message, sent_time FROM chat_logs WHERE chat_id = ? ORDER BY sent_time ASC;",
                        (chat_id,),
                    )
                else:
                    cur.execute(
                        "SELECT chat_id, name, role, message, sent_time FROM chat_logs WHERE chat_id = ? ORDER BY sent_time ASC LIMIT ?;",
                        (chat_id, limit),
                    )
                ret_rows = cur.fetchall()
        return ret_rows

    def get_character_personas(self, chat_id):
        # Get character persona from database
        ret_row = None
        with sqlite3.connect(self.db_path) as conn:
            with AutoCloseCursur(conn) as cur:
                cur.execute(
                    "SELECT persona,name FROM character where chat_id =?;", (chat_id,)
                )
                ret_row = cur.fetchall()
        return ret_row

    def update_character_persona(self, chat_id: str, name: str, persona: str):
        # Update character persona in database
        with sqlite3.connect(self.db_path) as conn:
            with AutoCloseCursur(conn) as cur:
                cur.execute(
                    "replace into character VALUES (?,?,?);",
                    (
                        chat_id,
                        persona,
                        name,
                    ),
                )
                cur.execute("delete from character where name isnull;")
            conn.commit()

    def delete_character_persona(
        self,
        chat_id: str,
        name: str,
    ):
        # Update character persona in database
        with sqlite3.connect(self.db_path) as conn:
            with AutoCloseCursur(conn) as cur:
                cur.execute(
                    "delete from character where chat_id=? and name = ?;",
                    (
                        chat_id,
                        name,
                    ),
                )
            conn.commit()

    def reset_character_persona(self, chat_id: str):
        # Get character persona from database
        with sqlite3.connect(self.db_path) as conn:
            with AutoCloseCursur(conn) as cur:
                cur.execute("delete from character where chat_id = ?;", (chat_id,))
            conn.commit()

    def get_member(self, chat_id: str):
        # Get character persona from database
        ret_row = None
        s_time = datetime.datetime.now()
        e_time = s_time + datetime.timedelta(seconds=-3)

        with sqlite3.connect(self.db_path) as conn:
            with AutoCloseCursur(conn) as cur:
                cur.execute(
                    "DELETE FROM membar WHERE time < ? and chat_id = ?;",
                    (e_time, chat_id),
                )
                cur.execute("SELECT name FROM membar where chat_id = ?;", (chat_id,))
                ret_row = cur.fetchall()
        return ret_row

    def insert_member(self, chat_id: str, name: str):
        # Get character persona from database
        t_now = datetime.datetime.now()
        with sqlite3.connect(self.db_path) as conn:
            with AutoCloseCursur(conn) as cur:
                cur.execute(
                    "insert into membar values(?, ?, ?);", (chat_id, t_now, name)
                )
                cur.fetchall()

    def delete_all_chat_logs(self, chat_id: str):
        # Delete all chat logs from database
        with sqlite3.connect(self.db_path) as conn:
            with AutoCloseCursur(conn) as cur:
                cur.execute("DELETE FROM chat_logs where chat_id=?;", (chat_id,))
            conn.commit()

    def get_room_num(self):
        with sqlite3.connect(self.db_path) as conn:
            with AutoCloseCursur(conn) as cur:
                cur.execute(
                    "SELECT COUNT(DISTINCT chat_id) AS unique_chat_ids_count FROM chat_logs;"
                )
                ret_row = cur.fetchone()
        return ret_row[0] if ret_row else [0]
    
    def run_query(query):
        with sqlite3.connect(self.db_path) as conn:
            with AutoCloseCursur(conn) as cur:
                cur.execute(
                    query
                )
                ret_row = cur.fetchall()
        return ret_row
    