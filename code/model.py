"""
Model build script
"""

import os
import time
import pandas as pd
import numpy as np
import tensorflow as tf

from keras import models, layers, optimizers, callbacks
from sklearn.model_selection import train_test_split
from sklearn.metrics import ( classification_report, accuracy_score, f1_score, roc_auc_score, precision_score, recall_score )

from utils import change_types, play_cols, player_cols, team_cols

def train_test_split_by_play(df):
    unique_plays = df['game_playid'].unique()
    train_plays, val_plays = train_test_split(unique_plays, test_size=0.2, random_state=42)
    train_df = df[df['game_playid'].isin(train_plays)].copy()
    val_df   = df[df['game_playid'].isin(val_plays)].copy()
    return train_df, val_df

def build_base_model(play_in, player_in, team_in, learning_rate=1e-3) -> models.Model:
    play_input   = tf.keras.Input(shape=(play_in,), name='play_input')
    player_input = tf.keras.Input(shape=(player_in,), name='player_input')
    team_input   = tf.keras.Input(shape=(team_in,), name='team_input')

    play_x   = layers.Dense(16, activation='relu')(play_input)
    player_x = layers.Dense(16, activation='relu')(player_input)
    team_x   = layers.Dense(32, activation='relu')(team_input)

    merged = layers.Concatenate()([play_x, player_x, team_x])
    x = layers.Dense(32, activation='relu')(merged)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(16, activation='relu')(x)

    output = layers.Dense(1, activation='sigmoid')(x)

    model = models.Model(inputs=[play_input, player_input, team_input], outputs=output)
    model.compile( optimizer=optimizers.Adam(learning_rate=learning_rate),
                   loss='binary_crossentropy',
                   metrics=['accuracy'] )
    return model

def train_base_model(csv_path, save_model_path) -> str:
    df = pd.read_csv(csv_path)
    df = change_types(df)

    df_train, df_val = train_test_split_by_play(df)

    X_play_t   = df_train[play_cols].values
    X_player_t = df_train[player_cols].values
    X_team_t   = df_train[team_cols].values
    y_t        = df_train['ran_route'].values

    X_play_v   = df_val[play_cols].values
    X_player_v = df_val[player_cols].values
    X_team_v   = df_val[team_cols].values
    y_v        = df_val['ran_route'].values

    model = build_base_model( play_in=X_play_t.shape[1],
                              player_in=X_player_t.shape[1],
                              team_in=X_team_t.shape[1],
                              learning_rate=1e-3 )

    model.fit( [X_play_t, X_player_t, X_team_t],
               y_t,
               validation_data=([X_play_v, X_player_v, X_team_v], y_v),
               epochs=5,
               batch_size=32 )

    model.save(save_model_path)
    return save_model_path

def incremental_training(base_model_path, stop_week, data_dir, save_dir):
    start_time = time.time()
    current_model_path = base_model_path

    df_all = pd.DataFrame()

    base_model = 'w1.csv'
    first_week_csv = os.path.join(data_dir, base_model)
    if os.path.isfile(first_week_csv):
        df_w1 = pd.read_csv(first_week_csv)
        df_w1 = change_types(df_w1)
        df_all = pd.concat([df_all, df_w1], ignore_index=True)

    for w in range(2, stop_week + 1):
        print(f"\n=== Week {w} ===")

        try:
            model = models.load_model(current_model_path)
        except Exception as e:
            print(f"Could not load model {current_model_path}.\nError: {e}")
            break

        csv_path = os.path.join(data_dir, f"w{w}.csv")
        if not os.path.isfile(csv_path):
            print(f"Week {w} data not found")
            continue

        df_week = pd.read_csv(csv_path)
        df_week = change_types(df_week)
        df_all = pd.concat([df_all, df_week], ignore_index=True)

        df_train, df_val = train_test_split_by_play(df_all)

        X_play_t   = df_train[play_cols].values
        X_player_t = df_train[player_cols].values
        X_team_t   = df_train[team_cols].values
        y_t        = df_train['ran_route'].values

        X_play_v   = df_val[play_cols].values
        X_player_v = df_val[player_cols].values
        X_team_v   = df_val[team_cols].values
        y_v        = df_val['ran_route'].values

        # Uncomment and re-compile model if you want to change something
        # model.compile( optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        #                loss='binary_crossentropy',
        #                metrics=['accuracy'] )

        callbacks_ = [ callbacks.EarlyStopping( monitor='val_loss', patience=1, restore_best_weights=True ),
                       callbacks.ModelCheckpoint( filepath=os.path.join(save_dir, f"best-w{w}.keras"),
                                                  monitor='val_accuracy',
                                                  save_best_only=True ) ]

        model.fit( [X_play_t, X_player_t, X_team_t],
                    y_t,
                    validation_data=([X_play_v, X_player_v, X_team_v], y_v),
                    epochs=3,
                    batch_size=32,
                    callbacks=callbacks_ )

        """
        Evaluation
        """
        y_val_prob = model.predict([X_play_v, X_player_v, X_team_v])
        y_val_pred = (y_val_prob > 0.5).astype(int).ravel()

        accuracy  = accuracy_score(y_v, y_val_pred)
        precision = precision_score(y_v, y_val_pred, zero_division=0)
        recall    = recall_score(y_v, y_val_pred, zero_division=0)
        f1_       = f1_score(y_v, y_val_pred, zero_division=0)
        roc_      = roc_auc_score(y_v, y_val_prob)

        print(f"Week {w} Validation Metrics:")
        print(f"  - Accuracy:  {accuracy:.4f}")
        print(f"  - Precision: {precision:.4f}")
        print(f"  - Recall:    {recall:.4f}")
        print(f"  - F1:        {f1_:.4f}")
        print(f"  - ROC AUC:   {roc_:.4f}")
        print(classification_report(y_v, y_val_pred, zero_division=0))

        # Save the final model for this week
        new_model_path = os.path.join(save_dir, f"week{w}.keras")
        model.save(new_model_path)
        current_model_path = new_model_path

    print(f"\n=== Done! Total time: {time.time() - start_time:.2f} seconds ===")

"""
Main Driver
"""
if __name__ == "__main__":
    data_path = "./data/processed"
    save_path = "./data/model/"

    # Train on the first week's data (with play-based splitting)
    base_model_path = train_base_model( csv_path=f"{data_path}/w1.csv",
                                        save_model_path=f"{save_path}/w1.keras" )

    incremental_training(base_model_path=base_model_path, stop_week=9, data_dir=data_path, save_dir=save_path)