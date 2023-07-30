import streamlit as st
from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx


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
                    
                    .header {
                          background: #fff;
                          display: flex;
                          top: 0;
                          height: 100px;
                          padding: 20px;
                          position: fixed;
                          justify-content: space-between;
                          width: 100%;
                        }
                    
                    </style>
                    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
