import numpy as np

def print_l():
    print('\n')
    for i in range(9):
        print('-', end=' ')

def change_types(tracking):
    tracking['game_playid'] = tracking['game_playid'].astype('category')
    tracking['ran_route'] = tracking['ran_route'].astype(np.uint8)
    tracking['frameid'] = tracking['frameid'].astype(np.uint16)
    tracking['frame_type'] = tracking['frame_type'].astype(np.int8)
    tracking['score_diff'] = tracking['score_diff'].astype(np.int8)
    tracking['quarter'] = tracking['quarter'].astype(np.uint8)
    tracking['down'] = tracking['down'].astype(np.uint8)
    tracking['game_clock'] = tracking['game_clock'].astype(np.uint16)
    tracking['yards_for_first'] = tracking['yards_for_first'].astype(np.uint8)
    tracking['yards_to_endzone'] = tracking['yards_to_endzone'].astype(np.uint8)
    tracking['nflid'] = tracking['nflid'].astype(np.uint16)
    tracking['x_rel_ball'] = tracking['x_rel_ball'].astype(np.float32)
    tracking['y_rel_ball'] = tracking['y_rel_ball'].astype(np.float32)
    tracking['sx'] = tracking['sx'].astype(np.float32)
    tracking['sy'] = tracking['sy'].astype(np.float32)
    tracking['orientation_std'] = tracking['orientation_std'].astype(np.float32)
    tracking['distance_to_ball'] = tracking['distance_to_ball'].astype(np.float32)

    for column in tracking.columns:
        if column.startswith('o_'):
            tracking[column] = tracking[column].astype(np.float32)

    return tracking

def rename_columns(plays, player_play, players, tracking):
    plays.rename(columns={'gameId': 'gameid', 'homeTeamAbbr': 'home_team',
                          'visitorTeamAbbr': 'away_team', 'playId': 'playid',
                          'yardsToGo': 'yards_for_first', 'possessionTeam': 'offense',
                          'defensiveTeam': 'defense', 'yardlineSide': 'yard_line_side',
                          'yardlineNumber': 'yard_line_num', 'gameClock': 'game_clock',
                          'preSnapHomeScore': 'home_score', 'preSnapVisitorScore': 'away_score',
                          'absoluteYardlineNumber': 'abs_yard_line', 'offenseFormation':'offense_formation',
                          'receiverAlignment': 'receiver_alignment',
                          'qbSpike': 'qb_spike', 'qbKneel': 'qb_kneel',
                          'qbSneak':'qb_sneak', 'rushLocationType': 'rush_location',
                          'penaltyYards':'penalty_yards', 'pff_runConceptPrimary': 'run_concept',
                          'pff_passCoverage':'pass_coverage', 'pff_manZone': 'man_zone'}, inplace=True)

    player_play.rename(columns={'gameId': 'gameid', 'playId': 'playid', 'nflId': 'nflid',
                                'teamAbbr': 'team', 'hadRushAttempt': 'had_rush_attempt',
                                'hadPassReception': 'had_pass_reception',
                                'wasTargettedReceiver': 'was_targetted_receiver',
                                'inMotionAtBallSnap': 'in_motion',
                                'shiftSinceLineset': 'shift_since_lineset',
                                'motionSinceLineset': 'motion_since_lineset',
                                'wasRunningRoute': 'ran_route', 'routeRan': 'route_ran',
                                'blockedPlayerNFLId1': 'blocked_nflid1',
                                'blockedPlayerNFLId2': 'blocked_nflid2',
                                'blockedPlayerNFLId3': 'blocked_nflid3',
                                'pff_primaryDefensiveCoverageMatchupNflId': 'coverage_nflid1',
                                'pff_secondaryDefensiveCoverageMatchupNflId': 'coverage_nflid2'}, inplace=True)
    
    players.rename(columns={'nflId': 'nflid'}, inplace=True)

    tracking.rename(columns={'gameId': 'gameid', 'playId': 'playid', 'nflId': 'nflid',
                             'frameId': 'frameid', 'frameType': 'frame_type',
                             'club': 'team', 'playDirection': 'play_direction',
                             's': 'speed', 'a': 'accel', 'dis': 'dist',
                             'o': 'orientation', 'dir': 'direction'}, inplace=True)

    return plays, player_play, players, tracking

play_cols = ['frameid', 'frame_type', 'score_diff', 'quarter', 'down', 'game_clock', 'yards_for_first', 'yards_to_endzone']
player_cols = ['position_enc', 'x_rel_ball', 'y_rel_ball', 'sx', 'sy', 'orientation_std', 'distance_to_ball']
team_cols = [
    'o_x_1', 'o_y_1','o_sx_1','o_sy_1','o_orien_1','o_dist_1',
    'o_x_2', 'o_y_2','o_sx_2','o_sy_2','o_orien_2','o_dist_2',
    'o_x_3', 'o_y_3','o_sx_3','o_sy_3','o_orien_3','o_dist_3',
    'o_x_4', 'o_y_4','o_sx_4','o_sy_4','o_orien_4','o_dist_4',
    'o_x_5', 'o_y_5','o_sx_5','o_sy_5','o_orien_5','o_dist_5',
    'o_x_6', 'o_y_6','o_sx_6','o_sy_6','o_orien_6','o_dist_6',
    'o_x_7', 'o_y_7','o_sx_7','o_sy_7','o_orien_7','o_dist_7',
    'o_x_8', 'o_y_8','o_sx_8','o_sy_8','o_orien_8','o_dist_8',
    'o_x_9', 'o_y_9','o_sx_9','o_sy_9','o_orien_9','o_dist_9',
    'o_x_10','o_y_10','o_sx_10','o_sy_10','o_orien_10','o_dist_10'
]