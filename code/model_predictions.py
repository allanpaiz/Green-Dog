"""
Script to save/view the models predictions
"""

import time
import pandas as pd
from keras import models
from sklearn.metrics import accuracy_score
from utils import change_types, play_cols, player_cols, team_cols

start_time = time.time()

# Loop through weeks 2 to 9
for week in range(2, 10):
    # Load model
    model_path = f'./model/week{week - 1}.keras'
    model = models.load_model(model_path)

    # Load data
    data_path = f'./data/processed/w{week}.csv'
    df = pd.read_csv(data_path)
    change_types(df)
    # df = df[~df['position_enc'].isin([4, 5, 6, 7, 10])]

    X_play = df[play_cols].values
    X_player = df[player_cols].values
    X_team = df[team_cols].values

    predictions = model.predict([X_play, X_player, X_team])
    df['pred_probability'] = predictions.flatten().round(4)
    df['pred_class'] = (df['pred_probability'] >= 0.5).astype(int)

    overall_accuracy = accuracy_score(df['ran_route'], df['pred_class'])
    print(f"Week {week - 1} Model - Overall Accuracy on Week {week} : {overall_accuracy:.4f}")

    # Comment out if you do not want to save the predictions
    df.drop(columns=team_cols, inplace=True)
    output_path = f'./data/predictions/w{week}.csv'
    df.to_csv(output_path, index=False)

print("--- %s seconds ---" % (time.time() - start_time))