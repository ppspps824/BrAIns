import datetime
import random

import openai
import streamlit as st
from st_click_detector import click_detector
from streamlit_autorefresh import st_autorefresh
from streamlit_extras.buy_me_a_coffee import button
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
    st.session_state.brains_action = "デフォルト"
    st.session_state.current_ai_name = ""


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
members = db.get_member(st.session_state.chat_id)
if members:
    members = [name[0] for name in members]
        
member_names = list(set(members)) + ai_list
member_names_text = ",".join(member_names)


def setting_header():
    if member_names_text:
        room_info=f"{st.session_state.chat_id} / {st.session_state.brains_action}"
        room_member=f"@{member_names_text}"
    else:
        room_info=f"{st.session_state.chat_id}"
        room_member="No Members"
        
    with st.container():
        st.markdown('<div class="floating_right"></div>', unsafe_allow_html=True)
        st.write("")
        st.button("🚪",on_click=back_to_main)
        if st.button("🤖"):
            switch_page("brains")
    
    with st.container():
        st.markdown('<div class="floating_left"></div>', unsafe_allow_html=True)
        st.caption(room_info)
        st.caption(room_member)

def back_to_main():
    st.session_state.chat_id = ""
    st.session_state.name = ""


if st.session_state.name:
    setting_header()
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
        user_msg = user_msg.replace("＠", "@").replace("@ ", "@")
        
        action_list=[]
        if "@" in user_msg:
            if "@all" in user_msg:
                action_list = ai_list.copy()
            else:
                action_list = [info for info in ai_list if f"@{info}" in user_msg]
        else:
            if len(ai_list):
                if st.session_state.brains_action == "キープ":
                    if st.session_state.current_ai_name:
                        action_list=[st.session_state.current_ai_name]
        
                if st.session_state.brains_action == "デフォルト":
                    action_list =random.sample(ai_list, random.randint(1, len(ai_list)))
        
        try:
            if action_list:
                if st.button("ストップ"):
                    st.experimental_rerun()
                    
            for num, current_ai_name in enumerate(action_list):
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
                        all_msg = all_msg.replace(f"@{current_ai_name}", "")
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
                        action_list.append(ai_name)
    
                st.session_state.current_ai_name = current_ai_name
        except:
            with st.chat_message("chatbot", avatar="assistant"):
            st.error("現在BrAInsを利用できません。")
            st.experimental_rerun()
            
    # Refresh the page every (REFRESH_INTERVAL) seconds
    count = st_autorefresh(
        interval=const.REFRESH_INTERVAL, limit=None, key="fizzbuzzcounter"
    )
else:
    st.image("resource/logo.jpg")
    with st.form("UserInfo"):
        input_name = st.text_input("Name")
        input_room_id = st.text_input("ルーム名を入力")

        if st.form_submit_button("Join"):
            st.session_state.chat_id = input_room_id
            if all([input_name, input_room_id]):
                if input_name not in member_names:
                    st.session_state.name = input_name
                    st.experimental_rerun()
                else:
                    st.warning("名前が他の参加者と重複しています。")
            else:
                st.warning("名前とルームIDを入力してください。")

    with st.expander("BrAInsとは"):
        st.write(
            """
        AI(BrAIn)参加型のマルチチャットです。
        
        ### 開始方法
        - 名前とルーム名を入力し、Joinボタンを押すとチャットが開始します。
        - ルーム名が既に存在する場合は参加となり、存在しない場合は新しいルームが作成されます。
        - ルーム名を共有することでチャットに参加してもらうことができます。
        
        ### チャット画面
        - ページ下部の入力欄にメッセージを入力することで発言できます。
        - BrAInを参加させるためには、右上の🤖よりコンフィグ画面に移動して設定します。
        - デフォルトではランダム応答となっており、@BrAIn名で個別応答、@allで全員応答になります。
        
        ### コンフィグ画面
        - チャット画面の右上にある🤖で表示できます。
        - ブレストや雑談などのプリセットから参加させるBrAInを選択したり、応答方法を選択できます。
        - また、BrAInsをランダム生成したり、独自のBrAInを設定することもできます。
        
        """
        )
        button(username="papasim824C", floating=False, width=221)
