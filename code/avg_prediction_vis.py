"""
Script to plot probabilities for Example 1
"""

import pandas as pd
import matplotlib.pyplot as plt

game_play_list = [ '2022091804_252',  '2022091804_678',  '2022091804_1293',
                   '2022092500_287',  '2022092500_2239', '2022092500_2582',
                   '2022100906_2267', '2022100906_2349', '2022100906_4218',
                   '2022101605_560',  '2022101605_1796', '2022101605_2925', 
                   '2022102000_2007', '2022102000_2073' ]

p_play = pd.read_csv('./data/comp/player_play.csv')
p_play.insert(0, 'game_playid', p_play['gameId'].astype(str) + '_' + p_play['playId'].astype(str))

preds = pd.read_csv('./data/predictions/combined.csv')
preds = preds[preds['game_playid'].isin(game_play_list)]
preds = p_play[p_play['game_playid'].isin(game_play_list)]

nflid_mapping = { '2022091804_252':  52513, '2022092500_287':  52513, '2022100906_2349': 52513,
                  '2022102000_2007': 43383, '2022091804_678':  52513, '2022091804_1293': 52513,
                  '2022092500_2239': 52513, '2022092500_2582': 52513, '2022100906_2267': 52513,
                  '2022100906_4218': 52513, '2022101605_560':  52513, '2022101605_1796': 52942,
                  '2022101605_2925': 52942, '2022102000_2073': 43383 }

filtered_preds = pd.DataFrame()
for game_playid, nflid in nflid_mapping.items():
    temp_df = preds[(preds['game_playid'] == game_playid) & (preds['nflid'] == nflid)]
    filtered_preds = pd.concat([filtered_preds, temp_df])

preds = filtered_preds
average_preds = preds.groupby(['game_playid', 'frameid'])['pred_probability'].mean().reset_index()
run_plays = []
pass_plays = []
target_play = pd.Series(dtype=float)

for game_playid in average_preds['game_playid'].unique():
    game_play_data = average_preds[average_preds['game_playid'] == game_playid]
    smoothed_data = game_play_data['pred_probability'].rolling(window=5, min_periods=1).mean().reset_index(drop=True)
    
    if game_playid == '2022102000_2073':
        target_play = game_play_data['pred_probability'].reset_index(drop=True)
        target_play = pd.concat([pd.Series([target_play.iloc[0]]), target_play], ignore_index=True)
        target_frame_ids = pd.concat([pd.Series([0]), game_play_data['frameid'].reset_index(drop=True)], ignore_index=True)
    elif game_playid in ['2022091804_252', '2022092500_287', '2022100906_2349', '2022102000_2007']:
        pass_plays.append(pd.concat([pd.Series([smoothed_data.iloc[0]]), smoothed_data], ignore_index=True))
    else:
        run_plays.append(pd.concat([pd.Series([smoothed_data.iloc[0]]), smoothed_data], ignore_index=True))

max_length = max(max(len(series) for series in pass_plays), max(len(series) for series in run_plays))

def pad_series(series, length):
    return pd.concat([series, pd.Series([None] * (length - len(series)))], ignore_index=True)

average_pass_plays = pd.concat([pad_series(s, max_length) for s in pass_plays], axis=1).mean(axis=1, skipna=True)
average_run_plays = pd.concat([pad_series(s, max_length) for s in run_plays], axis=1).mean(axis=1, skipna=True)

frame_ids = range(max_length)

fig, ax = plt.subplots()

scale_colors = { 0: ('white', 0.0, 0.248, 'Not Running Route'),
                 1: ('blue', 0.25, 0.498, 'Unlikely'),
                 2: ('yellow', 0.50, 0.748, 'Probable'),
                 3: ('orange', 0.75, 0.898, 'Likely'),
                 4: ('red', 0.90, 1.0, 'Running Route') }

for scale, (color, ymin, ymax, label) in scale_colors.items():
    if color == 'red':
        ax.axhspan(ymin, ymax, xmin=0, xmax=1, color=color, alpha=0.4)
    elif color == 'orange':
        ax.axhspan(ymin, ymax, xmin=0, xmax=1, color=color, alpha=0.3)
    elif color == 'yellow':
        ax.axhspan(ymin, ymax, xmin=0, xmax=1, color=color, alpha=0.2)
    else:
        ax.axhspan(ymin, ymax, xmin=0, xmax=1, color=color, alpha=0.1)

    ax.text(107, (ymin + ymax) / 2, scale_colors[scale][3].capitalize(), 
            verticalalignment='center', horizontalalignment='right', color='black', fontsize=10)

ax.plot(frame_ids, average_run_plays, color='green', linewidth=4, label='Run Plays')
ax.plot(frame_ids, average_pass_plays, color='royalblue', linewidth=4, label='Pass Plays')
ax.plot(target_frame_ids, target_play, color='red', linewidth=4, label='game_playid : 2022102000_2073')

ax.axvline(x=0, color='black', linestyle='--')
ax.text(-2, 0.5, 'line_set', rotation=90, color='black', fontsize=12, verticalalignment='center')

ax.legend(loc='upper left', framealpha=1.0, fontsize=11)
ax.set_xlabel('Frame')
ax.set_ylabel('Probability')
ax.set_ylim(0, 1)
ax.set_title('Average Predicted Route Probabilities')

plt.show()