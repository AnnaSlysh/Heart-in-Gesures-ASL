import streamlit as st
import utils

# NOTE: Replace the YouTube URLs below with real ASL alphabet tutorial videos.
# A great source is the "Bill Vicars" channel (ASL University) on YouTube —
# search each letter like "ASL letter A Bill Vicars" to find the right video ID.
ASL_VIDEO_PAIRS = {
    "Easy Level":  ["A", "B", "C", "D", "E", "F", "G", "H"],
    "Medium Level": ["I", "J", "K", "L", "M", "N", "O", "P"],
    "Hard Level":  ["Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"],
}

# Placeholder: replace values with real YouTube URLs for each letter
VIDEO_URLS = {
    "A": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "B": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "C": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "D": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "E": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "F": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "G": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "H": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "I": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "J": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "K": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "L": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "M": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "N": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "O": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "P": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "Q": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "R": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "S": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "T": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "U": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "V": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "W": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "X": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "Y": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
    "Z": "https://www.youtube.com/watch?v=tkMg8g8vVUo",
}


def app():
    utils.load_css("style.css")

    st.markdown('''
    <div class="page-hero">
        <div class="title_header">Learning Materials</div>
        <p>Videos and resources for learning the ASL alphabet</p>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown('<div class="section-tag">Useful Links</div>', unsafe_allow_html=True)
    st.markdown('''
    <div class="card"><div class="card-body">
        <a href="https://www.lifeprint.com/asl101/pages-signs/alphabet/alphabet.htm" target="_blank">ASL University — Free ASL Alphabet Reference (lifeprint.com)</a><br><br>
        <a href="https://www.handspeak.com/word/index.php?id=19" target="_blank">Handspeak — ASL Dictionary &amp; Alphabet</a><br><br>
        <a href="https://spreadthesign.com/en.us/search/?cls=1" target="_blank">Spread The Sign — ASL online sign dictionary</a>
    </div></div>
    ''', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    def render_video_section(label, letters):
        st.markdown(f'<div class="section-tag">{label}</div>', unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
        left_letters  = letters[::2]
        right_letters = letters[1::2]
        col1, col2 = st.columns(2)
        for col, items in [(col1, left_letters), (col2, right_letters)]:
            with col:
                for letter in items:
                    st.video(VIDEO_URLS[letter])
                    st.markdown(
                        f'<div class="letter-badge">{letter}</div>',
                        unsafe_allow_html=True
                    )
                    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

    for section_label, letters in ASL_VIDEO_PAIRS.items():
        render_video_section(section_label, letters)
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
