"""
Visualization script for example play
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

gpid = '2022110610_88'
save_to_csv = False
prefix = 'f_'
save_vis = True
playerid = 40011

gid, pid = map(int, gpid.split('_'))
comp_dir = './data/comp/'

def find_week(gid) -> str:
    games = pd.read_csv(f'{comp_dir}/games.csv')
    week = games.loc[games['gameId'] == gid, 'week'].iloc[0]

    return week

week = find_week(gid)
comp_tracking = pd.read_csv(f'{comp_dir}/tracking_week_{week}.csv')
play_tracking = comp_tracking[(comp_tracking['gameId'] == gid) & (comp_tracking['playId'] == pid)]

predictions = pd.read_csv('./data/predictions/combined.csv')
if gpid not in predictions['game_playid'].values:
    print(f"{gpid} not found in predictions")
    exit()

tracking_predictions = predictions[predictions['game_playid'] == gpid]
columns = [ 'game_playid', 'nflid', 'frameid', 'pred_probability']
play_predictions = tracking_predictions[columns]

play_tracking.insert(0, 'game_playid', play_tracking['gameId'].astype(str) + '_' + play_tracking['playId'].astype(str))
play_tracking = play_tracking.drop(columns=['gameId', 'playId'])
cols = ['nflId', 'frameId', 'frameType', 'displayName', 'jerseyNumber', 'event']
play_tracking = play_tracking.loc[:, cols]
play_tracking.rename(columns={'nflId': 'nflid', 'frameId': 'frameid', 'frameType': 'frame_type', 'displayName': 'name', 'jerseyNumber': 'number'}, inplace=True)
play_tracking['number'] = play_tracking['number'].fillna(0).astype(np.int8)

snap_frameid = play_tracking[play_tracking['frame_type'] == 'SNAP']['frameid'].max()
pred_frameid = play_predictions['frameid'].max()
line_set_frameid = (snap_frameid - pred_frameid) + 1

def recount_frameid(play_predictions, line_set_frameid):
    play_predictions = play_predictions.sort_values(by=['nflid', 'frameid'])
    play_predictions['frameid'] = play_predictions.groupby('nflid').cumcount() + line_set_frameid
    return play_predictions

play_predictions = recount_frameid(play_predictions, line_set_frameid)
df = pd.merge(play_predictions, play_tracking, on=['nflid', 'frameid'], how='left')

if save_to_csv:
    df.to_csv(f'./data/{gpid}_line_animation_data.csv', index=False)

def scale_probability(prob):
    if prob <= 0.24:
        return 0
    elif prob <= 0.49:
        return 1
    elif prob <= 0.74:
        return 2
    elif prob <= 0.89:
        return 3
    else:
        return 4

df['scale'] = df['pred_probability'].apply(scale_probability)

def animate_single_player(gpid, df, prefix, playerid, save=True):
    df = df[(df['game_playid'] == gpid) & (df['nflid'] == playerid)]

    fig, ax = plt.subplots(figsize=(10, 6))
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

        ax.text( df['frameid'].min() + 2, (ymin + ymax) / 2,
                 scale_colors[scale][3].capitalize(), 
                 verticalalignment='center',
                 horizontalalignment='left',
                 color='black', fontsize=10 )

    line_raw, = ax.plot([], [], color='black')

    ax.set_xlim(df['frameid'].min(), df['frameid'].max())
    ax.set_ylim(0, 1)
    ax.set_xlabel('Frame')
    ax.set_ylabel('Probability')
    ax.set_title(f'Predicted Route Probability')

    def init():
        line_raw.set_data([], [])
        return line_raw,

    def animate(frame):
        x = df['frameid'][:frame]
        y_raw = df['pred_probability'][:frame]
        line_raw.set_data(x, y_raw)

        return line_raw,

    frames = len(df['frameid'].unique()) + 30
    anim = FuncAnimation(fig, animate, init_func=init, frames=frames, interval=100, blit=True)

    if save:
        anim.save(f'./figures/{prefix}{gpid}_{playerid}.gif', writer='pillow', fps=10)
        plt.savefig(f'./figures/{prefix}{gpid}_{playerid}.jpeg')
    else:
        plt.show()

    return anim

anim_single_player = animate_single_player(gpid, df, prefix, playerid, save_vis)