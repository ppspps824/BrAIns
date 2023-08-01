import datetime
import random

import openai
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_extras.buy_me_a_coffee import button
from streamlit_extras.switch_page_button import switch_page

from modules import common
from modules.database import database

st.set_page_config(
    page_title="BrAIns", page_icon="🤖", initial_sidebar_state="collapsed"
)


class Brains:
    def __init__(self):
        common.hide_style()

        # Update the use_chatbot setting
        if "name" not in st.session_state:
            st.session_state.name = ""
            st.session_state.chat_id = ""
            st.session_state.brains_action = "Default"
            st.session_state.current_ai_name = ""
            st.session_state.language = "EN"

        self.db_instance = database.Database()
        self.personas = self.db_instance.get_character_personas(
            st.session_state.chat_id
        )
        self.ai_list = [info[1] for info in self.personas]
        self.assistants = "- " + "\n- ".join(
            [f"Name:{info[1]},Role:{info[0]}" for info in self.personas]
        )

        self.base_rueles = f"""
        You are an AI chatbot. Please follow the rules below to interact with us.
        ## Rules
        - Act according to your assigned role.
        - Do not duplicate other assistants comments, including those of others.
        - Identify the roles of other assistants and seek input from appropriate assistants.
        - Actively use figures and graphs as well as text
        - When generating figures and graphs, output them in graphviz format.
        - Mentions should be "@name".
        - Do not send mentions to yourself.

        ## List of Assistants
        {self.assistants}
        ## Role


        """
        members = self.db_instance.get_member(st.session_state.chat_id)
        if members:
            members = [name[0] for name in members]

        self.member_names = list(set(members)) + self.ai_list
        self.member_names_text = ",".join(self.member_names)

    def handler(self):
        if st.session_state.name:
            self.chat_room()
        else:
            self.front_page()

    def admin(self):
        sql = st.text_input("sql")
        if sql:
            result = self.db_instance.run_query(sql)
            st.dataframe(result)

    def visualizer(self, text: str):
        try:
            digraph_start = text.find("```") + 4
            if digraph_start:
                digraph_end = text.rfind("```") - 1
                digraph_text = text[digraph_start:digraph_end]
                st.graphviz_chart(digraph_text)
        except:
            pass
        try:
            if all(["https" in text,"youtu" in text]):
                url_start=text.find("https")
                url_end=text[url_start:].find(" ")
                if url_end>0:
                    url=text[url_start:url_end]
                else:
                    url=text[url_start:]
                st.video(url)
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

    def chat_room(self):
        self.setting_header()
        self.db_instance.insert_member(st.session_state.chat_id, st.session_state.name)

        messages = []
        # Get chatbot settings
        openai_api_key = st.secrets["OPENAI_API_KEY"]
        openai.api_key = openai_api_key

        name = st.session_state.name
        user_msg = st.chat_input(
            f"{st.session_state['name']}:", disabled=False if name else True
        )

        # Show old chat messages
        chat_log = self.db_instance.get_chat_log(
            chat_id=st.session_state.chat_id, limit=100
        )

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

                # 可視化チェック
                self.visualizer(log_message)

            if self.personas is not None:
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
                st.experimental_rerun()

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
                    action_list = self.ai_list.copy()
                else:
                    action_list = [
                        info for info in self.ai_list if f"@{info}" in user_msg
                    ]
            else:
                if len(self.ai_list):
                    if st.session_state.brains_action in ["Keep", "キープ"]:
                        if st.session_state.current_ai_name:
                            action_list = [st.session_state.current_ai_name]

                    if st.session_state.brains_action in ["Default", "デフォルト"]:
                        action_list = random.sample(
                            self.ai_list, random.randint(1, len(self.ai_list))
                        )

            try:
                if action_list:
                    if st.button(
                        "Stop" if st.session_state.language == "EN" else "ストップ"
                    ):
                        st.experimental_rerun()

                for current_ai_name in action_list:
                    all_msg = ""
                    ai_info = [
                        info for info in self.personas if info[1] == current_ai_name
                    ][0]
                    current_ai_name = ai_info[1]
                    ai_roles = ai_info[0]

                    # Show chatbot message
                    rule = [
                        {
                            "role": "system",
                            "content": self.base_rueles + "\n" + ai_roles,
                        }
                    ]
                    messages.append(
                        {"role": "assistant", "content": current_ai_name + " said "}
                    )
                    if len(messages) > 5:
                        messages.pop(1)

                    prompt = rule + messages
                    completion = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo", messages=prompt, stream=True
                    )

                    with st.chat_message("chatbot", avatar="assistant"):
                        msg_place = st.empty()
                        for msg in completion:
                            assistant_msg = msg["choices"][0]["delta"].get(
                                "content", ""
                            )
                            all_msg += assistant_msg
                            all_msg = all_msg.replace(f"@{current_ai_name}", "")
                            msg_place.write(current_ai_name + ":\n\n" + all_msg)

                    messages[-1]["content"] += all_msg

                    self.db_instance.insert_chat_log(
                        chat_id=st.session_state.chat_id,
                        name=current_ai_name,
                        role="assistant",
                        message=all_msg,
                        sent_time=datetime.datetime.now(),
                    )

                    # メンションチェック
                    for ai_name in self.ai_list:
                        if f"@{ai_name}" in all_msg:
                            action_list.append(ai_name)

                    st.session_state.current_ai_name = current_ai_name
            except:
                with st.chat_message("chatbot", avatar="assistant"):
                    api_error_msg = (
                        "BrAIns currently unavailable."
                        if st.session_state.language == "EN"
                        else "現在BrAInsを利用できません。"
                    )
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
        st.session_state.language = cols[1].selectbox(
            " ", options=["EN", "JP"], label_visibility="collapsed"
        )
        cols[0].image("resource/logo.jpg")
        room_num = self.db_instance.get_room_num()
        cols[1].caption(f"Number of Rooms :{room_num}")
        with st.form("UserInfo"):
            input_name = st.text_input(
                "Name",
                placeholder="Jones" if st.session_state.language == "EN" else "さとう",
            )
            input_room_id = st.text_input(
                "Room",
                placeholder="Jones Film Club"
                if st.session_state.language == "EN"
                else "映画同好会0101",
            )

            if st.form_submit_button("Join"):
                if all(
                    [
                        input_name == st.secrets["admin_id"],
                        input_room_id == st.secrets["admin_pass"],
                    ]
                ):
                    self.admin()
                else:
                    st.session_state.chat_id = input_room_id
                    if all([input_name, input_room_id]):
                        if input_name not in self.member_names:
                            st.session_state.name = input_name
                            st.experimental_rerun()
                        else:
                            st.warning("Name is duplicated with another participant.")
                    else:
                        st.warning("Enter your name and room name.")

        with st.expander(
            "About BrAIns" if st.session_state.language == "EN" else "BrAInsとは"
        ):
            if st.session_state.language == "EN":
                about_msg = """
                AI(BrAIn)-participating multi-chat.

            ### How to start
            - Enter your name and room name, and press Join button to start chatting.
            - If the room name already exists, you will be joined; if not, a new room will be created.
            - If the room name does not exist, a new room will be created.

            ### Chat Screen
            - You can speak by typing your message in the input field at the bottom of the page.
            - To join BrAIn, go to the configuration screen from 🤖 in the upper right corner and set it up.
            - The default setting is random response, with @BrAIn name for individual response and @all for everyone response.

            ### Config Screen
            - You can view it by 🤖 in the upper right corner of the chat screen.
            - You can select BrAIns to join from presets such as "Breast" and "Chat" and choose the response method.
            - You can also randomly generate BrAIns or set your own BrAIns.

            ### Donation Request
            - Due to the personal development of this service, we have set a limit on the amount of OpenAI API usage.
            - Therefore, if you exceed the monthly usage limit, AI functions will not be available.
            - Donations will be returned to the amount used.
            - Also, we are currently using GPT3.5 in order to have more users, but we are considering upgrading to GPT4 depending on how many people donate.
            - Please click the 👇 button to make a donation. 🙇‍♂️
                """
            elif st.session_state.language == "JP":
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
