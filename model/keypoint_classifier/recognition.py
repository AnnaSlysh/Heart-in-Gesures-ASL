#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import copy
import itertools

import streamlit as st
import numpy as np
import cv2 as cv
import mediapipe as mp

from model.keypoint_classifier.keypoint_classifier import KeyPointClassifier

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def process_letter():
    """Advance the game state based on the letter in session_state['recognized_letter']."""
    if not all(k in st.session_state for k in ("recognized_letter", "random_word", "letter_states", "current_index")):
        return
    letter = st.session_state["recognized_letter"].upper()
    word = st.session_state["random_word"]
    current_index = st.session_state["current_index"]

    if current_index >= len(word):
        return

    if letter == word[current_index]:
        st.session_state["letter_states"][current_index] = "correct"
        st.session_state["current_index"] = current_index + 1
        st.session_state["wrong_gesture"] = None
        if current_index + 1 >= len(word):
            st.session_state["game_won"] = True
    else:
        st.session_state["wrong_gesture"] = letter


def _calc_landmark_list(image, landmarks):
    image_width, image_height = image.shape[1], image.shape[0]
    landmark_point = []
    for landmark in landmarks.landmark:
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)
        landmark_point.append([landmark_x, landmark_y])
    return landmark_point


def _pre_process_landmark(landmark_list):
    temp = copy.deepcopy(landmark_list)
    base_x, base_y = temp[0]
    for pt in temp:
        pt[0] -= base_x
        pt[1] -= base_y
    flat = list(itertools.chain.from_iterable(temp))
    max_val = max(map(abs, flat)) or 1
    return [v / max_val for v in flat]


def process_frame(img_file_buffer):
    """Process a single frame from st.camera_input() and return (letter, debug_image).

    Returns (None, image) if no hand is detected.
    Labels from the ASL keypoint model are already English letters (A–Y).
    """
    import PIL.Image
    import io

    bytes_data = img_file_buffer.getvalue()
    pil_image  = PIL.Image.open(io.BytesIO(bytes_data)).convert("RGB")
    image      = np.array(pil_image)
    image      = cv.cvtColor(image, cv.COLOR_RGB2BGR)
    debug_image = copy.deepcopy(image)

    mp_hands = mp.solutions.hands
    hands    = mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )

    keypoint_classifier = KeyPointClassifier()
    _label_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keypoint_classifier_label.csv')
    with open(_label_path, encoding='utf-8-sig') as f:
        labels = [row[0] for row in csv.reader(f)]

    results = hands.process(cv.cvtColor(image, cv.COLOR_BGR2RGB))
    detected_letter = None

    if results.multi_hand_landmarks is not None:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            lm_list     = _calc_landmark_list(debug_image, hand_landmarks)
            pre_lm      = _pre_process_landmark(lm_list)
            sign_id     = keypoint_classifier(pre_lm)
            label       = labels[sign_id]

            # Draw bounding box
            lm_array = np.array([[p[0], p[1]] for p in lm_list])
            x, y, w, h = cv.boundingRect(lm_array)
            cv.rectangle(debug_image, (x, y), (x + w, y + h), (0, 0, 0), 1)

            # Draw hand connections
            mp.solutions.drawing_utils.draw_landmarks(
                debug_image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Draw label overlay
            cv.rectangle(debug_image, (x, y), (x + w, y - 22), (0, 0, 0), -1)
            info_text = handedness.classification[0].label + ':' + label
            cv.putText(debug_image, info_text, (x + 5, y - 4),
                       cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)

            detected_letter = label.upper()

    hands.close()
    return detected_letter, debug_image
