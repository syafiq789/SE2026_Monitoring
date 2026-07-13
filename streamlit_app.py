import streamlit as st

st.set_page_config(
    page_title="SE2026 Monitoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }

        header[data-testid="stHeader"] {
            display: none !important;
        }

        footer {
            display: none !important;
        }

        div[data-testid="stAppViewContainer"] {
            padding: 0 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

FLASK_URL = "http://localhost:5000"

# Streamlit versi terbaru
if hasattr(st, "iframe"):
    st.iframe(
        FLASK_URL,
        width="stretch",
        height=1100,
    )

# Kompatibilitas untuk Streamlit versi lama
else:
    import streamlit.components.v1 as components

    components.iframe(
        FLASK_URL,
        height=1100,
        scrolling=True,
    )