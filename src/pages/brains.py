import datetime
import json

import openai
import streamlit as st
from streamlit_extras.switch_page_button import switch_page

import const
from modules import common
from modules.database import database

common.hide_style()
db = database.Database()


def create_random_brains():
    prompt = [
        {
            "role": "system",
            "content": """
Please create 2-3 personas in the same format as the sample below.
Please do not explain the contents, etc., and output only the generated product.
- sample
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
    
""",
        }
    ]
    count = 0
    if st.button("中止"):
        st.stop()
    while True:
        with st.spinner(f"生成中:{count+1}回目"):
            result = openai.ChatCompletion.create(
                model=const.MODEL_NAME,
                messages=prompt,
            )
            count += 1
            try:
                gen_ai_set = json.loads(result["choices"][0]["message"]["content"])
                break
            except:
                continue

    return gen_ai_set

st.write("")
if st.button("Back to Chat"):
    switch_page("chat")

with st.expander("Config"):
    st.session_state.brains_action=st.selectbox("応答方法を選択",options=["デフォルト","キープ","メンション"],help="いずれのモードでもメンションで指定が可能")
    
    if st.session_state.brains_action=="メンション":
        st.write("「@名前」で個別、複数指定。「@all」で全員が応答。")
    elif st.session_state.brains_action=="キープ":
        st.write("直近に発言したbrAInが応答する。")
    elif st.session_state.brains_action=="デフォルト":
        st.write("ランダムにbrAInが応答する。")
    
    
    with open("src/pages/brains_info.json", "r", encoding="utf-8") as f:
        brains_info = json.loads(f.read())
    
    st.write("---")
    brains_options = list(brains_info.keys())
    preset = st.selectbox("プリセットを選ぶ", options=brains_options)
    
    if preset != "指定なし":
        if preset == "ランダム生成":
            ai_set = create_random_brains()
        else:
            ai_set = brains_info[preset]
    
        db.reset_character_persona(st.session_state.chat_id)
    
        for persona_name, discription in ai_set:
            db.update_character_persona(st.session_state.chat_id, persona_name, discription)
    
    
    st.write("---")
    st.write("BrAInを追加・更新、削除")
    persona_name = st.text_input(
            label="名前",
        )
    discription = st.text_area(
            label="役割",
        )
    if st.button("追加・更新"):
            # Set persona
        db.update_character_persona(st.session_state.chat_id, persona_name, discription)
        st.experimental_rerun()
    if st.button("削除"):
        db.delete_character_persona(st.session_state.chat_id, persona_name)
        st.experimental_rerun()
    
st.write("## BrAIns")
personas = db.get_character_personas(st.session_state.chat_id)
ai_list = "\n".join(f"|{info[1]}|{info[0]}|" for info in personas)
st.write(
    f"""\n
|名前|役割|
|---|---|
{ai_list}
"""
)
st.write("")

