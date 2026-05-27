import streamlit as st
import random
import time
import threading
from collections import Counter
import utils

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from model.keypoint_classifier import recognition
from model.dynamic_classifier.dynamic_classifier import model_exists as dynamic_model_exists
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import av
import cv2
import numpy as np
import copy
import itertools
import mediapipe as mp

DYNAMIC_LETTERS  = frozenset('JZ')
SEQUENCE_LENGTH  = 16
RECORD_INTERVAL  = 0.067   # ~15 fps — matches training data collection cadence


def _classify_jz_motion(sequence):
    """Heuristic: Z has ≥2 horizontal direction reversals with wide x-range; J is everything else."""
    FTX, FTY   = 16, 17
    NOISE      = 0.015
    xs = [frame[FTX] for frame in sequence]
    x_range = max(xs) - min(xs)
    reversals = 0
    prev_dir  = None
    for i in range(1, len(xs)):
        dx = xs[i] - xs[i - 1]
        if abs(dx) > NOISE:
            d = 1 if dx > 0 else -1
            if prev_dir is not None and d != prev_dir:
                reversals += 1
            prev_dir = d
    return 'Z' if (reversals >= 2 and x_range > 0.20) else 'J'


def _calc_landmark_list(image, landmarks):
    h, w = image.shape[:2]
    return [[min(int(lm.x * w), w - 1), min(int(lm.y * h), h - 1)]
            for lm in landmarks.landmark]

def _pre_process_landmark(landmark_list):
    tmp = copy.deepcopy(landmark_list)
    bx, by = tmp[0]
    for p in tmp:
        p[0] -= bx; p[1] -= by
    flat = list(itertools.chain.from_iterable(tmp))
    mx = max(map(abs, flat)) or 1
    return [v / mx for v in flat]


class DynamicGestureProcessor(VideoProcessorBase):
    """Button-triggered fixed-length recorder that mirrors the training data collector."""

    def __init__(self):
        import csv as _csv
        import os as _os
        from model.dynamic_classifier.dynamic_classifier import DynamicGestureClassifier
        self._lock       = threading.Lock()
        self._recording  = False
        self._seq        = []
        self._last_t     = 0.0
        self._result     = None
        self._load_error = None
        try:
            self._classifier = DynamicGestureClassifier()
            print("[DynamicGestureProcessor] dynamic classifier loaded OK", flush=True)
        except Exception as e:
            import traceback as _tb
            self._load_error = str(e)
            print(f"[DynamicGestureProcessor] load failed: {e}", flush=True)
            print(_tb.format_exc(), flush=True)
            self._classifier = None
        _label_path = _os.path.join(
            _os.path.dirname(_os.path.abspath(__file__)),
            '..', 'model', 'dynamic_classifier', 'dynamic_classifier_label.csv'
        )
        with open(_label_path, encoding='utf-8-sig') as f:
            self._labels = [row[0] for row in _csv.reader(f) if row]
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )

    def start_recording(self):
        with self._lock:
            self._recording = True
            self._seq       = []
            self._last_t    = 0.0

    def get_result(self):
        with self._lock:
            return self._result, len(self._seq)

    def is_recording(self):
        with self._lock:
            return self._recording

    def reset(self):
        with self._lock:
            self._recording = False
            self._seq       = []
            self._last_t    = 0.0
            self._result    = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)
        now = time.time()

        rgb     = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)
        processed = None
        if results.multi_hand_landmarks:
            lm_list   = _calc_landmark_list(img, results.multi_hand_landmarks[0])
            processed = _pre_process_landmark(lm_list)
            mp.solutions.drawing_utils.draw_landmarks(
                img, results.multi_hand_landmarks[0],
                mp.solutions.hands.HAND_CONNECTIONS)

        classify_now = False
        with self._lock:
            if self._recording and now - self._last_t >= RECORD_INTERVAL:
                self._last_t = now
                self._seq.append(processed if processed is not None else [0.0] * 42)
                if len(self._seq) >= SEQUENCE_LENGTH:
                    self._recording = False
                    classify_now    = True

        if classify_now:
            self._run_classify()

        with self._lock:
            recording = self._recording
            seq_len   = len(self._seq)
            result    = self._result

        if result:
            cv2.putText(img, f"OK: {result}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 220, 0), 2)
        elif recording:
            cv2.putText(img, f"Recording: {seq_len}/{SEQUENCE_LENGTH}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 200, 80), 2)
        elif not recording and seq_len > 0:
            cv2.putText(img, "No J/Z detected — try again",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 220), 1)
        else:
            cv2.putText(img, "Ready — press 'Record Gesture'",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (160, 160, 160), 1)

        cv2.putText(img, "Motion classifier: ON", (10, img.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 180, 0), 1)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    def _run_classify(self):
        if len(self._seq) < SEQUENCE_LENGTH:
            return
        label = _classify_jz_motion(self._seq[:SEQUENCE_LENGTH])
        with self._lock:
            self._result = label


def change_level(level):
    st.session_state.clear()
    st.session_state["level"] = level
    if level != "menu":
        reset_game()


def reset_game():
    levels = {
        "easy": (["CAT", "DOG", "HAT", "SUN", "MAP", "BIG", "CUP", "FAN", "HOP", "NET",
                  "RUN", "TIP", "WEB", "ARM", "BAT", "DIP", "EAR", "FIG", "GUM", "INK",
                  "LOG", "MOP", "NUT", "OAK", "PIN", "RIB", "SAP", "TON", "WAX", "YAM",
                  # words with dynamic letters (J, Z):
                  "JAB", "JAM", "JOY", "JOT", "ZAP", "ZIP", "ZOO"],),
        "medium": (["CAVE", "DIVE", "FROG", "GLOW", "HERO", "KING", "LIME", "MIST",
                    "OPEN", "PINK", "ROPE", "SLIM", "TREK", "URGE", "VIBE", "WISE",
                    "YELL", "BLUE", "CAMP", "DAWN", "FIND", "GROW", "HELP", "IRIS",
                    "BOLD", "CALM", "DESK", "EPIC", "MYTH", "NOVA", "PURE", "SOFT",
                    # words with dynamic letters:
                    "JUMP", "JOIN", "JUST", "ZERO", "ZONE", "GAZE", "HAZE", "MAZE"],),
        "hard": (["MAGIC", "NOBLE", "OCEAN", "PLANT", "RIVER", "STORM", "TOWER",
                  "UNITY", "VIVID", "WORLD", "YOUTH", "BRAVE", "CHARM", "DRIVE",
                  "ELITE", "FLAME", "GROVE", "HONOR", "INPUT", "KNACK", "LEARN",
                  "MONEY", "NERVE", "PROOF", "QUOTE", "ROBIN", "SCOUT", "TREND",
                  # words with dynamic letters:
                  "JUMPY", "MAJOR", "JEWEL", "JELLY", "BLAZE", "CRAZE", "FROZE",
                  "GRAZE", "OZONE", "PRIZE", "TOPAZ"],),
    }
    words = levels[st.session_state["level"]][0]
    word = random.choice(words)
    st.session_state["random_word"] = word
    st.session_state["current_index"] = 0
    st.session_state["letter_states"] = ["pending"] * len(word)
    st.session_state["wrong_gesture"] = None
    st.session_state["game_won"] = False
    st.session_state["recognized_letter"] = ""


def render_word(word, letter_states, current_index):
    parts = []
    for i, letter in enumerate(word):
        state = letter_states[i]
        if state == "correct":
            css_class = "word-letter correct"
        elif i == current_index:
            css_class = "word-letter current"
        else:
            css_class = "word-letter pending"
        parts.append(f'<div class="{css_class}">{letter}</div>')
    return f'<div class="word-display">{"".join(parts)}</div>'


def app():
    utils.load_css("style.css")

    if "level" not in st.session_state:
        st.session_state.level = "menu"

    if st.session_state.level == "menu":
        st.markdown('''
        <div class="page-hero">
            <div class="title_header">Game</div>
            <p>Choose a difficulty level and start playing</p>
        </div>
        ''', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        level_meta = [
            (col1, "Easy",   "Short common words",   "easy_button",   "easy"),
            (col2, "Medium", "Medium-length words",   "medium_button", "medium"),
            (col3, "Hard",   "Challenging words",     "hard_button",   "hard"),
        ]

        for col, name, desc, key, level in level_meta:
            with col:
                st.markdown(f'''
                <div class="level-header">
                    <div class="level-name">{name}</div>
                    <div class="level-desc">{desc}</div>
                </div>
                ''', unsafe_allow_html=True)
                st.button("Play", on_click=change_level, args=(level,), key=key, use_container_width=True)

    else:
        level_titles = {
            "easy":   "Easy Level",
            "medium": "Medium Level",
            "hard":   "Hard Level",
        }

        level = st.session_state.level
        st.markdown(f'<div class="title_subheader">{level_titles[level]}</div>', unsafe_allow_html=True)

        if "random_word" not in st.session_state or "letter_states" not in st.session_state:
            reset_game()

        word = st.session_state["random_word"]
        letter_states = st.session_state["letter_states"]
        current_index = st.session_state["current_index"]
        game_won = st.session_state.get("game_won", False)
        wrong_gesture = st.session_state.get("wrong_gesture")

        st.markdown(render_word(word, letter_states, current_index), unsafe_allow_html=True)
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        if game_won:
            st.markdown(
                '<div class="game-stat" style="text-align:center;margin-top:12px;">'
                '<div class="game-stat-value">Excellent! You spelled the whole word!</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("""
            <style>
            div[data-testid="stHorizontalBlock"]:has(div[data-testid="stCustomComponentV1"]) {
                align-items: stretch !important;
            }
            div[data-testid="stHorizontalBlock"]:has(div[data-testid="stCustomComponentV1"])
            > div[data-testid="stColumn"] {
                display: flex !important;
                flex-direction: column !important;
            }
            div[data-testid="stHorizontalBlock"]:has(div[data-testid="stCustomComponentV1"])
            > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {
                flex: 1 !important;
                display: flex !important;
                flex-direction: column !important;
            }
</style>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns(2)

            current_letter = word[current_index] if current_index < len(word) else None
            is_dynamic = current_letter in DYNAMIC_LETTERS if current_letter else False

            with col1:
                if is_dynamic:
                    ctx = webrtc_streamer(
                        key=f"dynamic_{current_letter}",
                        mode=WebRtcMode.SENDRECV,
                        video_processor_factory=DynamicGestureProcessor,
                        media_stream_constraints={"video": True, "audio": False},
                        async_processing=True,
                    )
                    if ctx.video_processor:
                        if ctx.video_processor._load_error:
                            st.error(f"Model not loaded: {ctx.video_processor._load_error}")

                        result, seq_len = ctx.video_processor.get_result()
                        recording       = ctx.video_processor.is_recording()

                        if result is not None:
                            # Valid J or Z detected — advance game
                            ctx.video_processor.reset()
                            st.session_state["recognized_letter"] = result
                            recognition.process_letter()
                            st.rerun()
                        elif recording:
                            # Actively collecting frames — show progress + Submit so user can
                            # force a rerender once the video overlay shows "OK: J/Z"
                            st.caption(f"Recording: {seq_len}/{SEQUENCE_LENGTH} frames — perform the gesture now...")
                            if st.button("Submit Gesture",
                                         key=f"submit_dyn_{current_index}",
                                         use_container_width=True):
                                st.rerun()  # re-check result after rerender
                        elif seq_len >= SEQUENCE_LENGTH:
                            # Recording finished but no J/Z detected
                            st.warning("Gesture not recognised as J or Z. Make sure your hand is fully visible and try again.")
                            if st.button("Try Again",
                                         key=f"retry_dyn_{current_index}",
                                         use_container_width=True):
                                ctx.video_processor.reset()
                                st.rerun()
                        else:
                            # Ready to start
                            if st.button("Record Gesture",
                                         key=f"rec_dyn_{current_index}",
                                         use_container_width=True):
                                ctx.video_processor.start_recording()
                                st.rerun()
                else:
                    import hashlib as _hl
                    img_file = st.camera_input(
                        "Show your gesture",
                        key=f"camera_{current_index}",
                    )
                    if img_file is not None:
                        photo_hash = _hl.md5(img_file.getvalue()).hexdigest()
                        if photo_hash != st.session_state.get("last_photo_hash"):
                            letter, _ = recognition.process_frame(img_file)
                            if letter:
                                st.session_state["last_photo_hash"] = photo_hash
                                st.session_state["recognized_letter"] = letter
                                recognition.process_letter()
                                st.rerun()
                            else:
                                st.warning("No hand detected. Please try again.")

            with col2:
                wrong_value = wrong_gesture if wrong_gesture else "&nbsp;"
                wrong_color = "hsl(0,60%,50%)" if wrong_gesture else "transparent"
                target_html = (
                    f'<div class="game-stat">'
                    f'<div class="game-stat-label">Show the gesture for</div>'
                    f'<div class="game-stat-value" style="font-size:56px;line-height:1.1;">{current_letter or ""}</div>'
                    f'</div>'
                ) if current_index < len(word) else ""
                wrong_html = (
                    f'<div class="game-stat">'
                    f'<div class="game-stat-label">Your gesture (incorrect)</div>'
                    f'<div class="game-stat-value" style="font-size:56px;line-height:1.1;color:{wrong_color};">{wrong_value}</div>'
                    f'</div>'
                )
                st.markdown(
                    f'<div style="display:flex;flex-direction:column;justify-content:space-between;height:100%;gap:12px;">'
                    f'{target_html}{wrong_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        st.button("Back to Menu", on_click=lambda: change_level("menu"), key="back_1button", use_container_width=True)
