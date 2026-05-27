import streamlit as st
import utils

def app():
    utils.load_css("style.css")

    st.markdown('''
    <div class="page-hero">
        <div class="title_header">Partners / NGOs</div>
        <p style="color:#ffffff; font-family:'Nunito',sans-serif; font-size:16px; margin-top:8px; font-weight:600;">
            Organisations supporting the Deaf and hard-of-hearing community
        </p>
    </div>
    ''', unsafe_allow_html=True)

    partners = [
        (
            "NAD — National Association of the Deaf",
            (
                "The <strong>National Association of the Deaf (NAD)</strong> is the oldest and largest national civil rights "
                "organization of, by, and for deaf and hard-of-hearing individuals in the United States, "
                "founded in <strong>1880</strong>. NAD advocates for full and equal access to society "
                "for over 48 million Americans with various degrees of hearing loss."
            ),
        ),
        (
            "Gallaudet University",
            (
                "Gallaudet University in Washington, D.C. is the world's only university designed to be <strong>barrier-free "
                "for deaf and hard-of-hearing students</strong>. Founded in <strong>1864</strong>, "
                "it is a global leader in ASL education, linguistics research, and deaf culture advocacy."
            ),
        ),
        (
            "ASL Connect",
            (
                "ASL Connect is a free, accessible online resource provided by Gallaudet University "
                "that teaches American Sign Language to learners of all levels. "
                "It offers structured ASL courses, video lessons, and <strong>interactive learning tools</strong> "
                "to make sign language education available to everyone worldwide."
            ),
        ),
    ]

    for title, body in partners:
        st.markdown(f'''
        <div class="partner-card">
            <div>
                <div class="partner-name">{title}</div>
                <div class="partner-body">{body}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
