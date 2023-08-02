import datetime

import streamlit as st
from st_supabase_connection import SupabaseConnection


class Database:
    def __init__(_self, connection_name: str = "init"):
        print("__init_")
        _self.supabase = _self.get_connection(connection_name)

    @st.cache_resource
    def get_connection(_self, connection_name):
        print("get_connection")
        supabase = st.experimental_connection(
            name=connection_name,
            type=SupabaseConnection,
            url=st.secrets["supabase_url"],
            key=st.secrets["supabase_key"],
        )
        return supabase

    def insert_chat_log(
        _self, chat_id: str, name: str, role: str, message: str, sent_time: str
    ):
        print("insert_chat_log")
        _self.supabase.table("chat_logs").insert(
            {
                "chat_id": chat_id,
                "name": name,
                "role": role,
                "message": message,
                "sent_time": int(sent_time.strftime("%Y%m%d%H%M%S%f")),
            }
        ).execute()

    def get_chat_log(_self, chat_id: str, limit: int = None):
        print("get_chat_log")
        ret_rows, error = (
            _self.supabase.table("chat_logs")
            .select("*")
            .eq("chat_id", chat_id)
            .order("sent_time")
            .execute()
        )
        return ret_rows[1]

    def get_character_personas(_self, chat_id):
        print("get_character_personas")
        # Get character persona from database
        ret_rows, error = (
            _self.supabase.table("character")
            .select("persona", "name")
            .eq("chat_id", chat_id)
            .execute()
        )
        return ret_rows[1]

    def update_character_persona(_self, chat_id: str, name: str, persona: str):
        print("update_character_persona")
        (
            _self.supabase.table("character")
            .upsert(
                {
                    "key": f"{chat_id}-{name}",
                    "chat_id": chat_id,
                    "persona": persona,
                    "name": name,
                },
                on_conflict="key",
            )
            .execute()
        )
        (
            _self.supabase.table("member")
            .upsert(
                {
                    "key": f"{chat_id}-{name}-99999999999999999999",
                    "chat_id": chat_id,
                    "name": name,
                    "time": 99999999999999999999,
                    "role": "assistant",
                },
                on_conflict="key",
            )
            .execute()
        )

        _self.supabase.table("character").delete().eq("name", None).execute()

    def delete_character_persona(
        _self,
        chat_id: str,
        name: str,
    ):
        # Update character persona in database
        _self.supabase.table("character").delete().eq(
            {
                "chat_id": chat_id,
                "name": name,
            }
        ).execute()

        _self.supabase.table("member").delete().eq(
            {
                "chat_id": chat_id,
                "name": name,
            }
        ).execute()

    def reset_character_persona(_self, chat_id: str):
        print("reset_character_persona")
        # Get character persona from database
        _self.supabase.table("character").delete().eq("chat_id", chat_id).execute()
        _self.supabase.table("member").delete().eq("chat_id", chat_id).eq(
            "role", "assistant"
        ).execute()

    def get_member(_self, chat_id: str):
        print("get_member")
        # Get character persona from database
        s_time = datetime.datetime.now()
        tmp_time = s_time + datetime.timedelta(seconds=-3)
        e_time = int(tmp_time.strftime("%Y%m%d%H%M%S%f"))

        _self.supabase.table("member").delete().lt("time", e_time).execute()

        ret_rows, error = (
            _self.supabase.table("member")
            .select("name")
            .eq("chat_id", chat_id)
            .execute()
        )

        return ret_rows[1]

    def insert_member(_self, chat_id: str, name: str):
        print("insert_member")
        print(chat_id, name)
        # Get character persona from database
        t_now = datetime.datetime.now()
        _self.supabase.table("member").insert(
            {
                "key": f'{chat_id}-{name}-{int(t_now.strftime("%Y%m%d%H%M%S%f"))}',
                "chat_id": chat_id,
                "time": int(t_now.strftime("%Y%m%d%H%M%S%f")),
                "name": name,
                "role": "user",
            }
        ).execute()

    def delete_all_chat_logs(_self, chat_id: str):
        print("delete_all_chat_logs")
        # Delete all chat logs from database
        _self.supabase.table("chat_logs").delete().eq("chat_id", chat_id).execute()

    def get_room_num(_self):
        print("get_room_num")
        ret_rows, error = _self.supabase.table("chat_logs").select("chat_id").execute()
        if ret_rows[1]:
            result = len(set([room_id["chat_id"] for room_id in ret_rows[1]]))
        else:
            result = 0
        return result
