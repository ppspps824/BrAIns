import streamlit as st


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
                    padding-top: 0rem;
                    }
                    [data-testid="stToolbar"] {visibility: hidden !important;}
                    footer {visibility: hidden !important;}
                    
                    div:has( >.element-container div.floating_right) {
                        display: flex;
                        text-align: right;
                        position: fixed;
                    }
                    
                    div.floating_right {
                        height:0%;
                    }
                    
                    div:has( >.element-container div.floating_left) {
                        display: flex;
                        flex-direction: column;
                        position: fixed;
                    }
                    
                    div.floating_left {
                        height:0%;
                    }
                    
                    </style>
                    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
