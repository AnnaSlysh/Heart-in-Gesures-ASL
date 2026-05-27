import streamlit as st
import GameRules
import Game
import Help
import AboutUs
import PublicOrganizations
import LearningMaterials
import utils

PAGES = {
    "About": AboutUs,
    "Game Rules": GameRules,
    "Learning Materials": LearningMaterials,
    "Game": Game,
    "Support the Project": Help,
    "Partners / NGOs": PublicOrganizations,
}

st.sidebar.title("Menu")
selection = st.sidebar.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")

page = PAGES[selection]
utils.load_css("style.css")
page.app()
