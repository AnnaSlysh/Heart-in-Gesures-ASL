import streamlit as st
import utils
import os

def app():
    utils.load_css("style.css")

    st.markdown('''
    <div class="page-hero">
        <div class="title_header">About Us</div>
        <p style="color:#ffffff; font-family:'Nunito',sans-serif; font-size:16px; margin-top:8px; font-weight:600;">
            Heart in Gestures — a game for learning the ASL alphabet
        </p>
    </div>
    ''', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        svg_path = "images/icon.svg"
        if os.path.exists(svg_path):
            st.image(svg_path, use_container_width=True)

    about_text = (
        "We are a group of teenagers participating in the international project <strong>Technovation Girls</strong>. "
        "We spent a long time choosing our topic and settled on inclusion. "
        "Our dream is to help people learn American Sign Language and make communication more accessible for everyone. "
        "This sparked the idea for an interactive game to teach the ASL fingerspelling alphabet, "
        "bringing together people from different cultures and backgrounds."
    )

    for title, body in [
        ("About the Project", about_text),
        ("Mission",  "To promote the development of an inclusive society where everyone has a voice."),
        ("Vision",   "A world where linguistic diversity is embraced as a strength, and every person — "
                     "regardless of their ability to hear — has equal access to communication, "
                     "education, and opportunities."),
        ("Goal",     "To help build an inclusive society where sign language is a natural part of interaction, "
                     "and technology becomes a means of equality, support, and mutual understanding."),
    ]:
        st.markdown(f'''
        <div class="card">
            <div class="card-title">{title}</div>
            <div class="card-body">{body}</div>
        </div>
        ''', unsafe_allow_html=True)
