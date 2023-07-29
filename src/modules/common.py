import streamlit as st
from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx
from streamlit_extras.buy_me_a_coffee import button


def get_session_id():
    return get_script_run_ctx().session_id


def hide_style():
    hide_streamlit_style = """
                    <style>
                    div[data-testid="stToolbar"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    div[data-testid="stDecoration"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    div[data-testid="stStatusWidget"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    #MainMenu {
                    visibility: hidden;
                    height: 0%;
                    }
                    header {
                    visibility: hidden;
                    height: 0%;
                    }
                    footer {
                    visibility: hidden;
                    height: 0%;
                    }
                    [data-testid="collapsedControl"] {
                        display: none
                    }
                    .block-container {
                    padding-top: 1rem;
                    }
                    [data-testid="stToolbar"] {visibility: hidden !important;}
                    footer {visibility: hidden !important;}
                    </style>
                    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    button(username="papasim824C", floating=True, width=221)
