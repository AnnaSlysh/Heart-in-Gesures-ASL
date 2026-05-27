#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Train a 2-class LSTM model for ASL dynamic letters J and Z.

Run from the Heart-in-Gesures-ASL directory:
    python train_asl_jz.py

Reads:  model/point_history_classifier/point_history.csv
Writes: model/dynamic_classifier/dynamic_classifier.tflite
        model/dynamic_classifier/dynamic_classifier_label.csv
"""

import csv
import os
import shutil

import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow as tf

RANDOM_SEED  = 42
NUM_CLASSES  = 2        # J=0, Z=1
TIME_STEPS   = 16
LANDMARK_DIM = 42
INPUT_DIM    = TIME_STEPS * LANDMARK_DIM   # 672

CSV_PATH   = 'model/point_history_classifier/point_history.csv'
OUT_DIR    = 'model/dynamic_classifier'
KERAS_PATH = f'{OUT_DIR}/dynamic_classifier.keras'
TFLITE_PATH = f'{OUT_DIR}/dynamic_classifier.tflite'
LABEL_PATH  = f'{OUT_DIR}/dynamic_classifier_label.csv'

# Original class indices in point_history.csv
J_IDX = 10
Z_IDX = 11


def load_data():
    """Load only J and Z rows, remap labels to 0=J and 1=Z."""
    X, y = [], []
    with open(CSV_PATH, encoding='utf-8') as f:
        for row in csv.reader(f):
            if not row:
                continue
            class_id = int(row[0])
            if class_id not in (J_IDX, Z_IDX):
                continue
            vals = [float(v) for v in row[1: INPUT_DIM + 1]]
            X.append(np.array(vals, dtype=np.float32).reshape(TIME_STEPS, LANDMARK_DIM))
            y.append(0 if class_id == J_IDX else 1)   # J→0, Z→1
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


def augment(X, y, factor=8, noise_sigma=0.02):
    """Multiply dataset with small Gaussian noise."""
    rng = np.random.default_rng(RANDOM_SEED)
    Xs, ys = [X], [y]
    for _ in range(factor - 1):
        noisy = X + rng.normal(0, noise_sigma, X.shape).astype(np.float32)
        Xs.append(noisy)
        ys.append(y)
    return np.concatenate(Xs), np.concatenate(ys)


def build_model():
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(TIME_STEPS, LANDMARK_DIM)),
        tf.keras.layers.LSTM(64, return_sequences=True),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.LSTM(32),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(NUM_CLASSES, activation='softmax'),
    ])
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'],
    )
    return model


def main():
    print('=== ASL J/Z Dynamic Gesture Trainer ===\n')
    print(f'Loading J and Z samples from {CSV_PATH} ...')
    X, y = load_data()
    print(f'  J samples: {int(np.sum(y == 0))}')
    print(f'  Z samples: {int(np.sum(y == 1))}')
    print(f'  Total:     {len(X)}\n')

    if len(X) < 10:
        print('ERROR: Not enough J/Z data. Run record_dynamic.py first.')
        return

    print(f'Augmenting {len(X)} samples x8 with small noise ...')
    X, y = augment(X, y, factor=8)
    print(f'After augmentation: {len(X)} samples\n')

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, train_size=0.75, random_state=RANDOM_SEED, stratify=y)
    print(f'Train: {len(X_train)}  |  Val: {len(X_test)}\n')

    model = build_model()
    model.summary()

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            KERAS_PATH, save_best_only=True, monitor='val_accuracy', verbose=1),
        tf.keras.callbacks.EarlyStopping(
            patience=25, restore_best_weights=True, verbose=1),
        tf.keras.callbacks.ReduceLROnPlateau(
            factor=0.5, patience=10, verbose=1),
    ]

    print('\nTraining ...')
    model.fit(
        X_train, y_train,
        epochs=300,
        batch_size=32,
        validation_data=(X_test, y_test),
        callbacks=callbacks,
        verbose=1,
    )

    val_loss, val_acc = model.evaluate(X_test, y_test, verbose=0)
    print(f'\nFinal validation accuracy: {val_acc * 100:.1f}%\n')

    best = tf.keras.models.load_model(KERAS_PATH)

    # Backup old model if present
    if os.path.exists(TFLITE_PATH):
        shutil.copy2(TFLITE_PATH, TFLITE_PATH.replace('.tflite', '_backup.tflite'))
        print(f'Old model backed up.')

    print('Converting to TFLite ...')
    converter = tf.lite.TFLiteConverter.from_keras_model(best)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS,
        tf.lite.OpsSet.SELECT_TF_OPS,
    ]
    converter._experimental_lower_tensor_list_ops = False
    tflite_bytes = converter.convert()

    with open(TFLITE_PATH, 'wb') as f:
        f.write(tflite_bytes)
    print(f'Model  -> {TFLITE_PATH}')

    # J=0, Z=1 — must match the label mapping in load_data()
    with open(LABEL_PATH, 'w', newline='', encoding='utf-8') as f:
        f.write('J\nZ\n')
    print(f'Labels -> {LABEL_PATH}')

    print('\nDone! Restart the Streamlit app to use the new model.')


if __name__ == '__main__':
    main()
