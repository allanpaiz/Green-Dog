"""
Data processing script
"""
import pandas as pd
import numpy as np
from utils import print_l, rename_columns, change_types
import time
import csv


start = time.time()

week = 9
comp_data_path = './data/comp/'

# Load data
games = pd.read_csv(f'{comp_data_path}games.csv')
player_play = pd.read_csv(f'{comp_data_path}player_play.csv')
players = pd.read_csv(f'{comp_data_path}players.csv')
plays = pd.read_csv(f'{comp_data_path}plays.csv')
tracking = pd.read_csv(f'{comp_data_path}tracking_week_{week}.csv')
print_l()
print(f'data loaded : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# Merge game and plays
plays = games.merge(plays, on='gameId', how='left')
print_l()
print(f'plays and games merged : {round(time.time() - start, 2)}')

# Rename columns
plays, p_play, players, tracking  = rename_columns(plays, player_play, players, tracking)
print_l()
print(f'columns renamed : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# Create `game_playid`
plays.insert(0, 'game_playid', plays['gameid'].astype(str) + '_' + plays['playid'].astype(str))
plays.drop(columns=['gameid', 'playid'], inplace=True)
p_play.insert(0, 'game_playid', p_play['gameid'].astype(str) + '_' + p_play['playid'].astype(str))
p_play.drop(columns=['gameid', 'playid'], inplace=True)
tracking.insert(0, 'game_playid', tracking['gameid'].astype(str) + '_' + tracking['playid'].astype(str))
tracking.drop(columns=['gameid', 'playid'], inplace=True)
print_l()
print(f'game_playid created : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# Remove AFTER_SNAP frames 
# Map frameType : BEFORE_SNAP: 0, SNAP: 1
tracking = tracking[tracking['frame_type'] != 'AFTER_SNAP'].reset_index(drop=True)
tracking['frame_type'] = tracking['frame_type'].map({'BEFORE_SNAP': 0, 'SNAP': 1})
print_l()
print(f'filtered and mapped \'AFTER_SNAP\' frames : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# Add player position data to tracking and integer-encode positions
tracking = tracking.merge(players[['nflid', 'position']], on='nflid', how='left')
position_mapping = { "WR": 1, "RB": 2, "TE": 3,
                     "T":  4, "G":  5, "QB": 6,
                     "C":  7, "FB": 8, "football": 9 }
tracking['position'] = tracking['position'].fillna('football')
tracking['nflid'] = tracking['nflid'].fillna(0).astype(int)
tracking['position_enc'] = tracking['position'].map(position_mapping).fillna(10).astype(int)
tracking.drop(columns=['position'], inplace=True)
print_l()
print(f'positions added and encoded : {round(time.time() - start, 2)} , Shape : {tracking.shape}')

# Label offense and defense
tracking = tracking.merge(plays[['game_playid', 'offense']], on='game_playid', how='left')
tracking['is_offense'] = tracking['team'] == tracking['offense']
tracking['is_defense'] = ~tracking['is_offense'] & (tracking['position_enc'] == 10)
tracking = tracking[~tracking['is_defense']]
tracking.drop(columns=['offense', 'is_defense'], inplace=True)
print_l()
print(f'offense labeled and defense dropped : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# Filter frames to only include frames after the 'line_set'
def filter_frames(df):
    frames = []
    grouped = df.groupby('game_playid')
    for game_playid, group in grouped:
        if 'line_set' in group['event'].values:
            min_frameid = group.loc[group['event'] == 'line_set', 'frameid'].min()
            group = group[group['frameid'] >= min_frameid]
        frames.append(group)
    return pd.concat(frames, ignore_index=True)

tracking = filter_frames(tracking)
tracking['frameid'] = tracking.groupby(['game_playid', 'nflid']).cumcount() + 1
print_l()
print(f'frameid count reset and filtered : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# remove qb_spike and qb_kneel plays
columns = ['qb_spike', 'qb_kneel']
mask = (plays['qb_spike'] == True) | (plays['qb_kneel'] == 1)
p_play = p_play[~p_play['game_playid'].isin(plays.loc[mask, 'game_playid'])]
tracking = tracking[~tracking['game_playid'].isin(plays.loc[mask, 'game_playid'])]
plays = plays[~mask].drop(columns=columns)
print_l()
print(f'qb spike/kneel plays removed : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# Remove plays with penalties
penalties = ~plays['penalty_yards'].isna()
p_play = p_play[~p_play['game_playid'].isin(plays.loc[penalties, 'game_playid'])]
tracking = tracking[~tracking['game_playid'].isin(plays.loc[penalties, 'game_playid'])]
plays = plays[~penalties]
plays.drop(columns=['penalty_yards'], inplace=True)
print_l()
print(f'penalties removed : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# Flag play direction
tracking['to_right'] = tracking['play_direction'].apply(lambda val: val.strip().lower() == 'right')
tracking.drop(columns=['play_direction'], inplace=True)
print_l()
print(f'play direction falgged : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# Standardize tracking data
tracking['xstd'] = tracking['x']
tracking['ystd'] = tracking['y']
tracking.loc[~tracking['to_right'], 'xstd'] = 120 - tracking.loc[~tracking['to_right'], 'x']
tracking.loc[~tracking['to_right'], 'ystd'] = (160/3) - tracking.loc[~tracking['to_right'], 'y']

tracking['direction_radians'] = np.radians(90 - tracking['direction'])
tracking['direction_std'] = tracking['direction_radians']
tracking.loc[~tracking['to_right'], 'direction_std'] = np.mod(np.pi + tracking.loc[~tracking['to_right'], 'direction_radians'], 2 * np.pi)
tracking.loc[tracking['is_offense'] & tracking['direction_std'].isna(), 'direction_std'] = 0.0
tracking.loc[~tracking['is_offense'] & tracking['direction_std'].isna(), 'direction_std'] = np.pi

tracking['orientation_radians'] = np.radians(90 - tracking['orientation'])
tracking['orientation_std'] = tracking['orientation_radians']
tracking.loc[~tracking['to_right'], 'orientation_std'] = np.mod(np.pi + tracking.loc[~tracking['to_right'], 'orientation_radians'], 2 * np.pi)
tracking.loc[tracking['is_offense'] & tracking['orientation_std'].isna(), 'orientation_std'] = 0.0
tracking.loc[~tracking['is_offense'] & tracking['orientation_std'].isna(), 'orientation_std'] = np.pi
print_l()
print(f'tracking data standardized : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# Create velocity vectors
tracking['sx'] = tracking['speed'] * np.cos(tracking['direction_std'])
tracking['sy'] = tracking['speed'] * np.sin(tracking['direction_std'])
print_l()
print(f'velocity vectors created : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# Add yards to endzone
tracking = tracking.merge(plays[['game_playid', 'yard_line_side', 'yard_line_num']], on='game_playid', how='left')
tracking['yards_to_endzone'] = np.where(tracking['yard_line_side'] == 'offense', 100 - tracking['yard_line_num'], tracking['yard_line_num'])
tracking.drop(columns=['yard_line_side', 'yard_line_num'], inplace=True)
print_l()
print(f'yards to endzone added : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# add play context
tracking = tracking.merge(plays[['game_playid', 'quarter', 'down', 'yards_for_first',
                                 'home_team', 'home_score', 'away_score','game_clock']], on='game_playid', how='left')
tracking['score_diff'] = np.where(tracking['team'] == tracking['home_team'], 
                                  tracking['home_score'] - tracking['away_score'], 
                                  tracking['away_score'] - tracking['home_score'])
tracking['game_clock'] = tracking['game_clock'].apply(lambda x: int(x.split(':')[0]) * 60 + int(x.split(':')[1]))
tracking.drop(columns=['home_team', 'home_score', 'away_score'], inplace=True)
print_l()
print(f'play context added : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# Flag ran route
p_play['ran_route'] = p_play['ran_route'].fillna(0)
tracking = tracking.merge(p_play[['game_playid', 'nflid', 'ran_route']], on=['game_playid', 'nflid'], how='left')
print_l()
print(f'ran route added : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# Add relative positions
ball_positions = tracking[tracking['position_enc'] == 9][['game_playid', 'frameid', 'xstd', 'ystd']]
ball_positions.rename(columns={'xstd': 'ball_x', 'ystd': 'ball_y'}, inplace=True)
tracking = tracking.merge(ball_positions, on=['game_playid', 'frameid'], how='left')
tracking['x_rel_ball'] = tracking['xstd'] - tracking['ball_x']
tracking['y_rel_ball'] = tracking['ystd'] - tracking['ball_y']
tracking['distance_to_ball'] = np.sqrt((tracking['xstd'] - tracking['ball_x'])**2 + (tracking['ystd'] - tracking['ball_y'])**2)
print_l()
print(f'relative positions to ball added : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# Drop football position
tracking = tracking[tracking['position_enc'] != 9]
print_l()
print(f'cya football : {round(time.time()  - start, 2)}, Shape : {tracking.shape}')

# Change data types 
change_types(tracking)
print_l()
print(f'dtypes set : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

columns_to_drop = [ 'displayName', 'time', 'jerseyNumber', 'team', 'x', 'y',
                    'speed', 'accel', 'direction', 'event', 'to_right',
                    'direction_radians', 'direction_std', 'dist','orientation',
                    'orientation_radians', 'is_offense', 'xstd','ystd', 'ball_x', 'ball_y' ]
tracking.drop(columns=columns_to_drop, inplace=True)
print_l()
print(f'columns dropped : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

# Mapping team state
cols_to_copy = [ 'game_playid', 'frameid', 'nflid', 'x_rel_ball', 'y_rel_ball',
                 'sx', 'sy', 'orientation_std', 'distance_to_ball' ]
offense_positions = tracking[cols_to_copy]
offense_positions = offense_positions.rename(columns={ 'x_rel_ball': 'o_x', 'y_rel_ball': 'o_y', 
                                                       'sx': 'o_sx', 'sy': 'o_sy', 
                                                       'orientation_std': 'o_orien', 
                                                       'distance_to_ball': 'o_dist' })
offense_positions['offender_id'] = offense_positions.groupby(['game_playid', 'frameid'], observed=True).cumcount() + 1
offense_positions_pivot = offense_positions.pivot_table(
    index=['game_playid', 'frameid'],
    columns='offender_id',
    values=['o_x', 'o_y', 'o_sx', 'o_sy', 'o_orien', 'o_dist'],
    observed=False,
    aggfunc='first'
)
offense_positions_pivot.columns = [f'{col[0]}_{col[1]}' for col in offense_positions_pivot.columns]
offense_positions_pivot.reset_index(inplace=True)
tracking = tracking.merge(offense_positions_pivot, on=['game_playid', 'frameid'], how='left')
for column in tracking.columns:
    if column.startswith('o_'):
        tracking[column] = tracking[column].astype(np.float32)
print_l()
print(f'team positions added : {round(time.time() - start, 2)}, Shape : {tracking.shape}')

ordered_columns = [
                # Keys
                'game_playid', 'nflid', 

                # Binary Target Variable
                # 1 := player ran a route
                # 0 := player did not run a route
                'ran_route',

                # Play Level Information
                'frameid', 'frame_type',
                'score_diff', 'quarter','down', 'game_clock',
                'yards_for_first', 'yards_to_endzone',

                # Player Information
                'position_enc',
                'x_rel_ball', 'y_rel_ball', 'sx', 'sy', 'orientation_std', 'distance_to_ball',
                 
                # Team Information
                # '0_x_1' := x relative to the ball
                # '0_y_1' := y relative to the ball
                # '0_sx_1' := x velocity 
                # '0_sy_1' := y velocity
                # '0_orien_1' := orientation
                # '0_dist_1' := distance to the ball
                'o_x_1', 'o_y_1', 'o_sx_1', 'o_sy_1', 'o_orien_1', 'o_dist_1',
                'o_x_2', 'o_y_2', 'o_sx_2', 'o_sy_2', 'o_orien_2', 'o_dist_2',
                'o_x_3', 'o_y_3', 'o_sx_3', 'o_sy_3', 'o_orien_3', 'o_dist_3',
                'o_x_4', 'o_y_4', 'o_sx_4', 'o_sy_4', 'o_orien_4', 'o_dist_4',
                'o_x_5', 'o_y_5', 'o_sx_5', 'o_sy_5', 'o_orien_5', 'o_dist_5',
                'o_x_6', 'o_y_6', 'o_sx_6', 'o_sy_6', 'o_orien_6', 'o_dist_6',
                'o_x_7', 'o_y_7', 'o_sx_7', 'o_sy_7', 'o_orien_7', 'o_dist_7',
                'o_x_8', 'o_y_8', 'o_sx_8', 'o_sy_8', 'o_orien_8', 'o_dist_8',
                'o_x_9', 'o_y_9', 'o_sx_9', 'o_sy_9', 'o_orien_9', 'o_dist_9',
                'o_x_10', 'o_y_10', 'o_sx_10', 'o_sy_10', 'o_orien_10', 'o_dist_10'
]
df = tracking[ordered_columns]
print_l()
print(f'final columns ordered : {round(time.time() - start, 2)}, Shape : {df.shape}')

# Save data
processed_path = './data/processed'
df.to_csv(f'{processed_path}/w{week}.csv', index=False)

end = time.time()
execution_time = end - start
print(f'Time: {execution_time}')