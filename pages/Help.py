import streamlit as st
import utils

def app():
    utils.load_css("style.css")

    st.markdown('''
    <div class="page-hero">
        <div class="title_header">Support the Project</div>
        <p>Together we build an inclusive future</p>
    </div>
    ''', unsafe_allow_html=True)

    cards = [
        ("Join Us",
         "Become part of our community — together we can change the world!<br><br>"
         "For questions and suggestions: "
         "<a href='mailto:heartingestures@gmail.com'>heartingestures@gmail.com</a>"),

        ("Your Feedback Matters",
         "<strong>Your opinion is important to us!</strong> "
         "If you have ideas for improving the game or want to share your impressions — write to us!<br><br>"
         "<a href='https://docs.google.com/forms/d/e/1FAIpQLScAlVmTQe6wKm4U7bqtnEbU8pravDP0XuGnP7ZlMWWw9SPSHA/viewform?usp=header' target='_blank'>Send Feedback</a>"),

        ("Spread the Word",
         "Tell your friends about our project, share it on social media or at events. "
         "This helps us find a new audience and potential partners.<br><br>"
         "<a href='https://www.instagram.com/heartingestures_/profilecard/?igsh=bHd2bGJnaWg4Ynp4' target='_blank'>Our Instagram</a>"),

        ("Partnership",
         "We are open to cooperation with organisations that share our values!<br>"
         "Write to us: "
         "<a href='mailto:heartingestures@gmail.com'>heartingestures@gmail.com</a>"),
    ]

    for title, body in cards:
        st.markdown(f'''
        <div class="card">
            <div class="card-title">{title}</div>
            <div class="card-body">{body}</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown(
        '<div class="card"><div class="card-body" style="text-align:center;">Respectfully, Grlpwr Team</div></div>',
        unsafe_allow_html=True,
    )
