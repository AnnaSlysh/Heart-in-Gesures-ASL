#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Live dynamic gesture recorder for Dynamic-Gestures-Training.

Shows your camera, press SPACE to record one 16-frame gesture sequence.
Each press = one training sample saved to point_history.csv.
Captures all 21 hand landmarks (42 values) per frame → 672 values per sample.

Run from the Dynamic-Gestures-Training directory:
    python record_dynamic.py --class_id 0

Controls:
    SPACE  - Record one gesture sequence (16 frames)
    r      - Undo last saved sample
    q      - Quit
"""

import argparse
import copy
import csv
import itertools
import os
import sys
import time

import cv2 as cv
import mediapipe as mp
import numpy as np

SEQUENCE_LENGTH  = 16
RECORD_INTERVAL  = 0.067   # ~15 fps recording
LANDMARK_DIM     = 42      # 21 landmarks × 2 (x, y)
CSV_PATH         = 'model/point_history_classifier/point_history.csv'
LABEL_PATH       = 'model/point_history_classifier/point_history_classifier_label.csv'


def load_labels():
    if not os.path.exists(LABEL_PATH):
        return []
    with open(LABEL_PATH, encoding='utf-8-sig') as f:
        return [row[0] for row in csv.reader(f) if row]


def calc_landmark_list(image, landmarks):
    h, w = image.shape[:2]
    pts = []
    for lm in landmarks.landmark:
        pts.append([min(int(lm.x * w), w - 1),
                    min(int(lm.y * h), h - 1)])
    return pts


def pre_process_landmark(landmark_list):
    """Normalize all 21 landmarks relative to wrist, scale by max extent. Returns 42 floats."""
    tmp = copy.deepcopy(landmark_list)
    base_x, base_y = tmp[0]
    for p in tmp:
        p[0] -= base_x
        p[1] -= base_y
    flat = list(itertools.chain.from_iterable(tmp))
    mx = max(map(abs, flat)) or 1
    return [v / mx for v in flat]


def count_existing_samples(class_id):
    if not os.path.exists(CSV_PATH):
        return 0
    count = 0
    with open(CSV_PATH, encoding='utf-8') as f:
        for row in csv.reader(f):
            if row and int(row[0]) == class_id:
                count += 1
    return count


def save_sample(class_id, flat_list):
    with open(CSV_PATH, 'a', newline='') as f:
        csv.writer(f).writerow([class_id, *flat_list])


def remove_last_sample(class_id):
    if not os.path.exists(CSV_PATH):
        return False
    with open(CSV_PATH, encoding='utf-8') as f:
        rows = list(csv.reader(f))
    for i in range(len(rows) - 1, -1, -1):
        if rows[i] and int(rows[i][0]) == class_id:
            rows.pop(i)
            with open(CSV_PATH, 'w', newline='') as f:
                csv.writer(f).writerows(rows)
            return True
    return False


def draw_ui(frame, label, class_id, count, status, progress):
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv.rectangle(overlay, (0, 0), (w, 110), (0, 0, 0), -1)
    cv.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    cv.putText(frame, label, (w // 2 - len(label) * 14, 60),
               cv.FONT_HERSHEY_SIMPLEX, 1.8, (100, 255, 150), 3, cv.LINE_AA)
    cv.putText(frame, f"Class {class_id}   Samples: {count}",
               (15, 25), cv.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1, cv.LINE_AA)

    color = (80, 200, 80) if 'RECORD' in status else \
            (80, 180, 255) if 'SAVED' in status else \
            (80, 80, 255)  if 'NO HAND' in status else (180, 180, 180)
    cv.putText(frame, status, (15, 90),
               cv.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv.LINE_AA)

    if progress > 0:
        bar_w = int((w - 24) * progress / SEQUENCE_LENGTH)
        cv.rectangle(frame, (12, h - 20), (12 + bar_w, h - 6), (80, 200, 80), -1)
        cv.rectangle(frame, (12, h - 20), (w - 12, h - 6), (120, 120, 120), 1)

    cv.putText(frame, "SPACE=record   r=undo   q=quit",
               (15, h - 30), cv.FONT_HERSHEY_SIMPLEX, 0.55, (140, 140, 140), 1, cv.LINE_AA)
    return frame


def main():
    labels = load_labels()
    if not labels:
        print(f"Error: label file not found at {LABEL_PATH}")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('--class_id', required=True, type=int,
                        help=f'Class index 0-{len(labels)-1}: ' +
                             '  '.join(f'{i}={l}' for i, l in enumerate(labels)))
    args = parser.parse_args()

    if not 0 <= args.class_id < len(labels):
        print(f"Error: class_id must be 0-{len(labels)-1}")
        sys.exit(1)

    label = labels[args.class_id]
    count = count_existing_samples(args.class_id)

    print(f"\n=== Recording: {label} (class {args.class_id}) ===")
    print(f"Each sample = {SEQUENCE_LENGTH} frames × {LANDMARK_DIM} values = {SEQUENCE_LENGTH * LANDMARK_DIM} values")
    print(f"Existing samples: {count}")
    print("SPACE=record   r=undo   q=quit\n")

    cap = cv.VideoCapture(0, cv.CAP_DSHOW)
    cap.set(cv.CAP_PROP_FRAME_WIDTH,  960)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 540)

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.5,
    )

    recording  = False
    seq_buffer = []   # list of 42-value landmark vectors
    last_cap_t = 0.0
    status     = 'READY'

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv.flip(frame, 1)

        image_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results   = hands.process(image_rgb)

        finger_tip  = None
        landmarks42 = None
        if results.multi_hand_landmarks:
            lm_raw      = results.multi_hand_landmarks[0]
            lm_list     = calc_landmark_list(frame, lm_raw)
            finger_tip  = lm_list[8]            # used for NO HAND DETECTED check
            landmarks42 = pre_process_landmark(lm_list)  # 42 floats
            mp.solutions.drawing_utils.draw_landmarks(
                frame, lm_raw, mp_hands.HAND_CONNECTIONS)

        now = time.time()

        if recording:
            if now - last_cap_t >= RECORD_INTERVAL:
                last_cap_t = now
                seq_buffer.append(landmarks42 if landmarks42 else [0.0] * LANDMARK_DIM)
                status = f'RECORDING  {len(seq_buffer)} / {SEQUENCE_LENGTH}'

            if len(seq_buffer) >= SEQUENCE_LENGTH:
                # Flatten: 16 frames × 42 values = 672 floats
                flat = [v for frame_lm in seq_buffer for v in frame_lm]
                save_sample(args.class_id, flat)
                count     += 1
                recording  = False
                seq_buffer = []
                status     = f'SAVED  ({count} total)'
                print(f"  Sample {count} saved  ({SEQUENCE_LENGTH * LANDMARK_DIM} values)")
        else:
            status = 'READY — press SPACE' if finger_tip else 'NO HAND DETECTED'

        frame = draw_ui(frame, label, args.class_id, count, status, len(seq_buffer))
        cv.imshow(f'Record dynamic: {label}', frame)

        key = cv.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' ') and not recording:
            recording  = True
            seq_buffer = []
            last_cap_t = time.time()
            status     = 'RECORDING...'
        elif key == ord('r') and not recording:
            if remove_last_sample(args.class_id):
                count -= 1
                print(f"  Removed last sample ({count} remaining)")

    hands.close()
    cap.release()
    cv.destroyAllWindows()

    print(f"\nDone. Samples for '{label}' (class {args.class_id}): {count}")


if __name__ == '__main__':
    main()
