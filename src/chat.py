import datetime
import os
import random
import string
import sys
import traceback

import openai
import streamlit as st
from dotenv import load_dotenv
from modules import common
from modules.database import database
from streamlit_autorefresh import st_autorefresh
from streamlit_extras.buy_me_a_coffee import button
from streamlit_extras.switch_page_button import switch_page

# .envファイルを読み込み
load_dotenv(verbose=True)

st.set_page_config(
    page_title="BrAIns", page_icon="🤖", initial_sidebar_state="collapsed"
)


class Brains:
    def __init__(self):
        common.hide_style()

        # Update the use_chatbot setting
        if "name" not in st.session_state:
            print("session_state init")
            st.session_state.name = ""
            st.session_state.chat_id = ""
            st.session_state.brains_action = "Default"
            st.session_state.current_ai_name = ""
            st.session_state.personas = []
            st.session_state.ai_list = []
            st.session_state.assistants = ""
            st.session_state.base_rueles = ""

        self.db_instance = database.Database(st.session_state.chat_id)

        self.member_names = []
        self.member_names_text = ""

    def create_random_room_name(self):
        n = 10
        res = "".join(
            [random.choice(string.ascii_letters + string.digits) for i in range(n)]
        )
        return res

    def get_members(self):
        members = self.db_instance.get_member(st.session_state.chat_id)
        if members:
            members = [name["name"] for name in members]

        self.member_names = list(set(members))
        self.member_names_text = ",".join(self.member_names)

    def handler(self):
        if st.session_state.name:
            self.chat_room()
        else:
            self.front_page()

    def visualizer(self, text: str):
        try:
            graph_text = text.replace("graphviz", "").replace("diagraph", "graph")
            digraph_start = graph_text.find("```") + 4
            if digraph_start:
                digraph_end = graph_text.rfind("```") - 1
                digraph_text = graph_text[digraph_start:digraph_end]
                st.graphviz_chart(digraph_text)
        except:
            pass
        try:
            if "http" in text:
                if "youtu" in text:
                    url_start = text.find("https")
                    url_end = text[url_start:].find(" ")
                    if url_end > 0:
                        url = text[url_start:url_end]
                    else:
                        url = text[url_start:]
                    st.video(url)
                else:
                    st.image(url)
        except:
            pass

    def setting_header(self):
        if self.member_names_text:
            room_info = f"{st.session_state.chat_id} / {st.session_state.brains_action}"
            room_member = f"@{self.member_names_text}"
        else:
            room_info = f"{st.session_state.chat_id}"
            room_member = "No Members"

        with st.container():
            cols = st.columns([10, 1, 1])
            cols[2].button("🚪", on_click=self.back_to_main)
            if cols[1].button("🤖"):
                switch_page("brains")
            st.caption(room_info)
            st.caption(room_member)
            st.markdown('<div class="floating_right"></div>', unsafe_allow_html=True)

    def back_to_main(self):
        st.session_state.chat_id = ""
        st.session_state.name = ""
        st.session_state.brains_action = "Default"
        st.session_state.current_ai_name = ""
        st.session_state.personas = []
        st.session_state.ai_list = []
        st.session_state.assistants = ""
        st.session_state.base_rueles = ""

    def chat_room(self):
        self.get_members()
        self.setting_header()
        self.db_instance.insert_member(st.session_state.chat_id, st.session_state.name)

        messages = []
        # Get chatbot settings
        openai.api_key = os.environ.get("OPENAI_API_KEY")

        name = st.session_state.name
        user_msg = st.chat_input(
            f"{st.session_state['name']}:", disabled=False if name else True
        )

        # Show old chat messages
        chat_log = self.db_instance.get_chat_log(
            chat_id=st.session_state.chat_id, limit=100
        )

        for msg_info in chat_log:
            log_name = msg_info["name"]
            log_role = msg_info["role"]
            log_message = msg_info["message"]
            # Show chat message

            if log_role == "assistant":
                avater = "assistant"
            else:
                avater = None
            with st.chat_message(log_name, avatar=avater):
                st.write(log_name + ":\n\n" + log_message)

                # 可視化チェック
                self.visualizer(log_message)

            if st.session_state.personas is not None:
                if log_role == "assistant":
                    messages.append({"role": "assistant", "content": log_message})
                else:
                    messages.append(
                        {
                            "role": "user",
                            "content": log_name + " said " + log_message,
                        }
                    )
                if len(messages) > 5:
                    messages.pop(1)

        if user_msg:
            if user_msg in ["All Clear", "オールクリア"]:
                self.db_instance.delete_all_chat_logs(st.session_state.chat_id)
                st.rerun()

            self.db_instance.insert_chat_log(
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

            action_list = []
            if "@" in user_msg:
                if "@all" in user_msg:
                    action_list = st.session_state.ai_list.copy()
                else:
                    action_list = [
                        info
                        for info in st.session_state.ai_list
                        if f"@{info}" in user_msg
                    ]
            else:
                if len(st.session_state.ai_list):
                    if st.session_state.brains_action in ["Keep", "キープ"]:
                        if st.session_state.current_ai_name:
                            action_list = [st.session_state.current_ai_name]

                    if st.session_state.brains_action in ["Default", "デフォルト"]:
                        action_list = random.sample(
                            st.session_state.ai_list,
                            random.randint(1, len(st.session_state.ai_list)),
                        )

            try:
                if action_list:
                    if st.button("ストップ"):
                        st.rerun()

                for current_ai_name in action_list:
                    print(current_ai_name)
                    all_msg = ""
                    ai_info = [
                        info
                        for info in st.session_state.personas
                        if info["name"] == current_ai_name
                    ][0]
                    current_ai_name = ai_info["name"]
                    ai_roles = ai_info["persona"]

                    # Show chatbot message
                    rule = [
                        {
                            "role": "system",
                            "content": st.session_state.base_rueles + "\n" + ai_roles,
                        }
                    ]
                    messages.append(
                        {"role": "assistant", "content": current_ai_name + " said "}
                    )
                    if len(messages) > 5:
                        messages.pop(1)

                    prompt = rule + messages
                    completion = openai.chat.completions.create(
                        model="gpt-4o", messages=prompt, stream=True
                    )

                    with st.chat_message("chatbot", avatar="assistant"):
                        st.write(current_ai_name + ":\n\n")
                        assistant_msg = st.write_stream(completion).replace(
                            f"@{current_ai_name}", ""
                        )

                    messages[-1]["content"] += assistant_msg

                    self.db_instance.insert_chat_log(
                        chat_id=st.session_state.chat_id,
                        name=current_ai_name,
                        role="assistant",
                        message=assistant_msg,
                        sent_time=datetime.datetime.now(),
                    )

                    # メンションチェック
                    for ai_name in st.session_state.ai_list:
                        if f"@{ai_name}" in all_msg:
                            action_list.append(ai_name)

                    st.session_state.current_ai_name = current_ai_name
            except Exception as e:
                t, v, tb = sys.exc_info()
                print(traceback.format_exception(t, v, tb))
                print(traceback.format_tb(e.__traceback__))
                print(e.args)
                with st.chat_message("chatbot", avatar="assistant"):
                    api_error_msg = "現在BrAInsを利用できません。"
                    st.error(api_error_msg)
                    self.db_instance.insert_chat_log(
                        chat_id=st.session_state.chat_id,
                        name=current_ai_name,
                        role="assistant",
                        message=api_error_msg,
                        sent_time=datetime.datetime.now(),
                    )

        st_autorefresh(interval=2000, limit=None, key="fizzbuzzcounter")

    def front_page(self):
        cols = st.columns([6, 1])
        cols[0].image("resource/logo.jpg")
        room_num = self.db_instance.get_room_num()
        cols[1].write("")
        cols[1].caption(f"Number of Rooms :{room_num}")
        with st.form("UserInfo"):
            input_name = st.text_input(
                "Name",
                placeholder="さとう",
            )
            if st.session_state.chat_id:
                value = st.session_state.chat_id
            else:
                value = self.create_random_room_name()

            input_room_id = st.text_input("Room", placeholder="映画同好会0101")

            if st.form_submit_button("Join"):
                self.get_members()
                st.session_state.chat_id = input_room_id
                if all([input_name, input_room_id]):
                    if input_name not in self.member_names:
                        st.session_state.name = input_name
                        st.rerun()
                    else:
                        st.warning("Name is duplicated with another participant.")
                else:
                    st.warning("Enter your name and room name.")

        with st.expander("BrAInsとは"):
            about_msg = """
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
            
            ### 寄付のお願い
            - 当サービスは個人開発のため、OpenAI API使用量に制限を設けています。
            - そのため、毎月の使用量制限を超過するとAI機能は利用不可となります。
            - 寄付いただいた分は使用量に還元いたします。
            - また、現在は多くの方にご利用いただくためにGPT3.5を利用していますが、寄付の状況を見てGPT4へのグレードアップも検討しております。
            - 是非👇のボタンより寄付をお願いいたます🙇‍♂️
            """

            st.write(about_msg)
            button(username="papasim824C", floating=False, width=221)
            st.caption("Powered by Streamlit, ChatGPT API.")


if __name__ == "__main__":
    brains = Brains()
    brains.handler()
