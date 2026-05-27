import streamlit as st
import utils

def app():
    utils.load_css("style.css")

    rules = [
        "Choose a difficulty level. The game is built on gestures of the <strong>ASL (American Sign Language) alphabet</strong>. You have unlimited attempts.",
        "A camera window will appear — perform hand gestures and the system will recognise them using a hand skeleton model powered by MediaPipe.",
        "Gestures are recognised <strong>regardless of which hand</strong> you use.",
        "A word is shown on screen. You must reproduce each letter in order, left to right.",
        "For <strong>static letters (A–Y, except J)</strong>: hold your hand still, then press <strong>Take a photo</strong>. The system instantly classifies the pose.",
        "For <strong>dynamic letters (J and Z)</strong>, which involve motion: press <strong>Record Gesture</strong>, perform the sign over ~2 seconds, and the system classifies the movement sequence.",
        "If a gesture is already captured, it will be marked as already captured.",
        "The game is available in <strong>English only</strong>.",
    ]

    st.markdown('''
    <div class="page-hero">
        <div class="title_header">Game Rules</div>
        <p style="color:#ffffff; font-family:'Nunito',sans-serif; font-size:16px; margin-top:8px; font-weight:600;">
            How to play Heart in Gestures — ASL
        </p>
    </div>
    ''', unsafe_allow_html=True)

    for i, rule in enumerate(rules):
        st.markdown(f'''
        <div class="step-card">
            <div class="step-number">{i + 1}</div>
            <div class="step-text">{rule}</div>
        </div>
        ''', unsafe_allow_html=True)
