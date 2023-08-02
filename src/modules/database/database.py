import datetime

import streamlit as st
from st_supabase_connection import SupabaseConnection


class Database:
    def __init__(self, connection_name: str = "init"):
        self.supabase = st.experimental_connection(
            name=connection_name,
            type=SupabaseConnection,
            url=st.secrets["supabase_url"],
            key=st.secrets["supabase_key"],
        )

    def insert_chat_log(
        self, chat_id: str, name: str, role: str, message: str, sent_time: str
    ):
        self.supabase.table("chat_logs").insert(
            {
                "chat_id": chat_id,
                "name": name,
                "role": role,
                "message": message,
                "sent_time": int(sent_time.strftime("%Y%m%d%H%M%S%f")),
            }
        ).execute()

    def get_chat_log(self, chat_id: str, limit: int = None):
        ret_rows, error = (
            self.supabase.table("chat_logs")
            .select("*")
            .eq("chat_id", chat_id)
            .order("sent_time")
            .execute()
        )
        return ret_rows[1]

    def get_character_personas(self, chat_id):
        # Get character persona from database
        ret_rows, error = (
            self.supabase.table("character")
            .select("persona", "name")
            .eq("chat_id", chat_id)
            .execute()
        )
        return ret_rows[1]

    def update_character_persona(self, chat_id: str, name: str, persona: str):
        (
            self.supabase.table("character")
            .upsert(
                {"chat_id": chat_id, "persona": persona, "name": name},
                on_conflict="name",
            )
            .execute()
        )

        self.supabase.table("character").delete().eq("name", None).execute()

    def delete_character_persona(
        self,
        chat_id: str,
        name: str,
    ):
        # Update character persona in database
        self.supabase.table("character").delete().eq(
            {
                "chat_id": chat_id,
                "name": name,
            }
        ).execute()

    def reset_character_persona(self, chat_id: str):
        # Get character persona from database
        self.supabase.table("character").delete().eq("chat_id", chat_id).execute()

    def get_member(self, chat_id: str):
        # Get character persona from database
        s_time = datetime.datetime.now()
        tmp_time = s_time + datetime.timedelta(seconds=-3)
        e_time = int(tmp_time.strftime("%Y%m%d%H%M%S%f"))

        self.supabase.table("member").delete().lt("time", e_time).execute()

        ret_rows, error = (
            self.supabase.table("member")
            .select("name")
            .eq("chat_id", chat_id)
            .execute()
        )

        return ret_rows[1]

    def insert_member(self, chat_id: str, name: str):
        # Get character persona from database
        t_now = datetime.datetime.now()
        self.supabase.table("member").insert(
            {
                "chat_id": chat_id,
                "time": int(t_now.strftime("%Y%m%d%H%M%S%f")),
                "name": name,
            }
        ).execute()

    def delete_all_chat_logs(self, chat_id: str):
        # Delete all chat logs from database
        self.supabase.table("chat_logs").delete().eq("chat_id", chat_id).execute()

    def get_room_num(self):
        ret_rows, error = self.supabase.table("chat_logs").select("chat_id").execute()
        if ret_rows[1]:
            result = len(set([room_id["chat_id"] for room_id in ret_rows[1]]))
        else:
            result = 0
        return result
