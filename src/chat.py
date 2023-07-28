# This page is for chat
import datetime
import os
import time

import openai
import streamlit as st
from PIL import Image
from streamlit_autorefresh import st_autorefresh
from streamlit_extras.switch_page_button import switch_page

import const
from modules import common
from modules.database import database

st.set_page_config(
    page_title="BrAIns", page_icon="🤖", initial_sidebar_state="collapsed"
)
common.hide_style()

# Update the use_chatbot setting
if "name" not in st.session_state:
    st.session_state.name = ""
    st.session_state.chat_id = ""


db = database.Database()
personas = db.get_character_personas(st.session_state.chat_id)
ai_list = [info[1] for info in personas]
llm = None
use_chatbot = False
assistants = "- " + "\n- ".join([f"Name:{info[1]},Role:{info[0]}" for info in personas])

base_rueles = f"""
You are an AI chatbot. Please follow the rules below to interact with us.
## Rules
- Act according to your assigned role.
- Do not duplicate other assistants comments, including those of others.
- Identify the roles of other assistants and seek input from appropriate assistants.
- Mentions should be "@name".
- Do not send mentions to yourself.

## List of Assistants
{assistants}
## Role


"""


def back_to_top():
    st.session_state.chat_id = ""
    st.session_state.name = ""
    st.experimental_rerun()


col1, col2 = st.columns([8, 2])

members = db.get_member(st.session_state.chat_id)
if members:
    members = members[0]
member_names = list(set(members)) + ai_list
member_names_text = ",".join(member_names)

if st.session_state.name:
    with col1:
        st.image("resource/logo.jpg")
        if st.session_state.name:
            if member_names_text:
                st.caption(f"{st.session_state.chat_id} ：@{member_names_text}")
            else:
                st.caption(f"{st.session_state.chat_id} ：No Members")
    with col2:
        if st.session_state.chat_id:
            st.write("")
            st.write("")
            select_option = st.selectbox("Options", options=["", "Config", "Exit"])
            if select_option == "Config":
                switch_page("brains")
            if select_option == "Exit":
                back_to_top()

    db.insert_member(st.session_state.chat_id, st.session_state.name)

    messages = []
    # Get chatbot settings
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    openai.api_key = openai_api_key
    if openai_api_key is None:
        personas = None
        st.error(
            "OPENAI_API_KEY is not set in the environment variables. Please contact the administrator."
        )

    user_infos = {}
    name = st.session_state.name
    user_msg = st.chat_input(
        f"{st.session_state['name']}:", disabled=False if name else True
    )

    # Show old chat messages
    chat_log = db.get_chat_log(
        chat_id=st.session_state.chat_id, limit=const.MAX_CHAT_LOGS
    )
    if chat_log is not None:
        for msg_info in chat_log:
            (
                log_chat_id,
                log_name,
                log_role,
                log_message,
                log_sent_time,
            ) = msg_info
            # Show chat message

            if log_role == "assistant":
                avater = "assistant"
            else:
                avater = None
            with st.chat_message(log_name, avatar=avater):
                st.write(log_name + ":\n\n" + log_message)

            if personas is not None:
                # Added conversation to give to chatbot.
                if log_role == "assistant":
                    messages.append({"role": "assistant", "content": log_message})
                else:
                    messages.append(
                        {
                            "role": "user",
                            "content": log_name + " said " + log_message,
                        }
                    )
                if len(messages) > const.MAX_CONVERSATION_BUFFER:
                    messages.pop(1)

    else:
        st.error(const.ERR_MSG_GET_CHAT_LOGS)

    # Show user message
    if user_msg:
        if user_msg == "オールクリア":
            db.delete_all_chat_logs(st.session_state.chat_id)
            st.experimental_rerun()
        # Show new chat message
        db.insert_chat_log(
            chat_id=st.session_state.chat_id,
            name=name,
            role="user",
            message=user_msg,
            sent_time=datetime.datetime.now(),
        )

        with st.chat_message(name, avatar=None):
            st.write(name + ":\n\n" + user_msg)

        messages.append({"role": "user", "content": name + " said " + user_msg})
        user_msg = user_msg.replace("＠", "@")
        if "@all" in user_msg:
            mention_list = ai_list.copy()
        else:
            mention_list = [info for info in ai_list if f"@{info}" in user_msg]
        if mention_list:
            if st.button("ストップ"):
                st.experimental_rerun()
        for num, current_ai_name in enumerate(mention_list):
            all_msg = ""
            ai_info = [info for info in personas if info[1] == current_ai_name][0]
            current_msg = messages[-1]["content"]
            current_ai_name = ai_info[1]
            ai_roles = ai_info[0]

            # Show chatbot message
            rule = [{"role": "system", "content": base_rueles + "\n" + ai_roles}]
            messages.append(
                {"role": "assistant", "content": current_ai_name + " said "}
            )
            if len(messages) > const.MAX_CONVERSATION_BUFFER:
                messages.pop(1)
            prompt = rule + messages
            completion = openai.ChatCompletion.create(
                model=const.MODEL_NAME, messages=prompt, stream=True
            )

            with st.chat_message("chatbot", avatar="assistant"):
                msg_place = st.empty()
                for msg in completion:
                    assistant_msg = msg["choices"][0]["delta"].get("content", "")
                    all_msg += assistant_msg
                    msg_place.write(current_ai_name + ":\n\n" + all_msg)

            messages[-1]["content"] += all_msg

            db.insert_chat_log(
                chat_id=st.session_state.chat_id,
                name=current_ai_name,
                role="assistant",
                message=all_msg,
                sent_time=datetime.datetime.now(),
            )
            # メンションチェック
            for ai_name in ai_list:
                if f"@{ai_name}" in all_msg:
                    mention_list.append(ai_name)

    # Refresh the page every (REFRESH_INTERVAL) seconds
    count = st_autorefresh(
        interval=const.REFRESH_INTERVAL, limit=None, key="fizzbuzzcounter"
    )
else:
    st.image("resource/logo.jpg")
    with st.form("UserInfo"):
        input_name = st.text_input("Name")
        tabs=st.tabs(["Open","Private"])
        with tabs[1]:
            select_room_id = st.text_input("ルームIDを入力")
        with tabs[0]:
            if not select_room_id:
                select_room_id = st.selectbox("ルームを選択", options=["Room1", "Room2", "Room3"])
        if st.form_submit_button("Join"):
            st.session_state.chat_id = select_room_id
            if input_name:
                if input_name not in member_names:
                    st.session_state.name = input_name
                    st.experimental_rerun()
                else:
                    st.warning("名前が他の参加者と重複しています。")
            else:
                st.warning("名前を入力してください。")
