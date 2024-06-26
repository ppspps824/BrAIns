import json

import openai
import streamlit as st
from modules import common
from modules.database import database
from streamlit_extras.switch_page_button import switch_page

print("brains")
common.hide_style()
db_instance = database.Database()


def create_random_brains():
    sample = """
[
    [
      "ボブ",
      "性別: 男性 年齢: 40代 職業: サラリーマン 趣味: 映画鑑賞、旅行、料理 特徴: 社交的で人懐っこい性格"
    ],
    [
      "カレン",
      "性別: 女性 年齢: 30代 職業: フリーランスのイラストレーター 趣味: 絵を描くこと、音楽を聴くこと、カフェ巡り 特徴: 明るく社交的な性格で、人と話すことが大好きです。話題は広範囲で、最新の映画や音楽、旅行のエピソードなどにも詳しいです。また、自分の絵についても熱心に語ることがあります。"
    ],
    [
      "タクヤ",
      "性別: 男性 年齢: 50代 職業: パートタイムのドライバー 趣味: 車のメンテナンス、釣り、写真撮影 特徴: 無口で物静かな性格ですが、人間観察が得意で、気づいたことなどを面白おかしく話すことがあります。特に車に関しては詳しく、最新車のトレンドやカスタマイズについても熱心に話すことがあります。"
    ]
  ]
    
"""

    prompt = [
        {
            "role": "system",
            "content": f"""
Please create 2-3 personas in the same format as the sample below.
Please do not explain the contents, etc., and output only the generated product.
- sample
{sample}
""",
        }
    ]
    count = 0
    if st.button("中止"):
        st.stop()

    correct = False
    gen_ai_set = {}
    for count in range(3):
        with st.spinner(f"Generating...:{count+1}"):
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=prompt,
            )
            try:
                gen_ai_set = json.loads(response.choices[0].message.content)
                return gen_ai_set
            except:
                continue
    if not correct:
        st.write("Please Retry😢")
        st.stop()


st.write("")
if st.button("Back to Chat"):
    switch_page("chat")

with st.expander("Config"):
    brains_action_options = ["デフォルト", "キープ", "メンション"]
    brains_action_label = "応答方法"
    brains_action_help = "いずれのモードでもメンションの利用が可能です。"
    brains_action_mention = "「@名前」で個別、複数指定。「@all」で全員が応答します。"
    brains_action_keep = "直近に発言したBrAInが応答します。"
    brains_action_random = "BrAIn達がランダムに応答します。"

    st.session_state.brains_action = st.selectbox(
        brains_action_label, options=brains_action_options, help=brains_action_help
    )

    if st.session_state.brains_action in ["Mention", "メンション"]:
        st.write(brains_action_mention)
    elif st.session_state.brains_action in ["Keep", "キープ"]:
        st.write(brains_action_keep)
    elif st.session_state.brains_action in ["Default", "デフォルト"]:
        st.write(brains_action_random)

    with open("src/pages/brains_info.json", "r", encoding="utf-8") as f:
        brains_info = json.loads(f.read())

    st.write("---")
    brains_options = list(brains_info.keys())
    preset = st.selectbox("Presets", options=brains_options)

    if preset not in ["Nothing", "指定なし"]:
        if preset in ["Generating", "ランダム生成"]:
            ai_set = create_random_brains()
        else:
            ai_set = brains_info[preset]

        db_instance.reset_character_persona(st.session_state.chat_id)

        for persona_name, discription in ai_set:
            db_instance.update_character_persona(
                st.session_state.chat_id, persona_name, discription
            )

    st.write("---")
    st.write("BrAInを追加・更新、削除")
    persona_name = st.text_input(
        label="名前",
    )
    discription = st.text_area(
        label="役割",
    )
    if st.button("Add or Update"):
        # Set persona
        db_instance.update_character_persona(
            st.session_state.chat_id, persona_name, discription
        )
        st.experimental_rerun()
    if st.button("Delete"):
        db_instance.delete_character_persona(st.session_state.chat_id, persona_name)
        st.experimental_rerun()

st.write("## BrAIns")

st.session_state.personas = db_instance.get_character_personas(st.session_state.chat_id)
if st.session_state.personas:
    st.session_state.ai_list = [info["name"] for info in st.session_state.personas]
    st.session_state.assistants = "- " + "\n- ".join(
        [
            f'Name:{info["name"]},Role:{info["persona"]}'
            for info in st.session_state.personas
        ]
    )
else:
    st.session_state.ai_list = []
    st.session_state.assistants = ""

st.session_state.base_rueles = f"""
You are an AI chatbot. Please follow the rules below to interact with us.
## Rules
- Act according to your assigned role.
- Do not duplicate other assistants comments, including those of others.
- Identify the roles of other assistants and seek input from appropriate assistants.
- Actively use figures and graphs as well as text
- When generating figures and graphs, output them in graphviz format.
- Mentions should be "@name".
- Do not send mentions to your

## List of Assistants
{st.session_state.assistants}
## Role
"""
ai_list = "\n".join(
    f'|{info["name"]}|{info["persona"]}|' for info in st.session_state.personas
)
st.write(f"""\n
|名前|役割|
|---|---|
{ai_list}
""")
st.write("")
