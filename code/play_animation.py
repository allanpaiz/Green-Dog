"""
Modified play animation for example play.

Source: https://www.kaggle.com/code/nickwan/animate-plays-with-plotly-real-no-lies-here
"""
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils import colors, scale_colors

project_dir = './data/comp/'

def hex_to_rgb_array(hex_color):
    return np.array(tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)))

def ColorDistance(hex1,hex2):
    if hex1 == hex2:
        return 0
    rgb1 = hex_to_rgb_array(hex1)
    rgb2 = hex_to_rgb_array(hex2)
    rm = 0.5*(rgb1[0]+rgb2[0])
    d = abs(sum((2+rm,4,3-rm)*(rgb1-rgb2)**2))**0.5
    return d

def ColorPairs(team1,team2):
    color_array_1 = colors[team1]
    color_array_2 = colors[team2]

    if ColorDistance(color_array_1[0],color_array_2[0])<500:
        return { team1:[color_array_1[0],color_array_1[1]],
                 team2:[color_array_2[1],color_array_2[0]],
                 'football':colors['football'] }
    else:
        return { team1:[color_array_1[0],color_array_1[1]],
                 team2:[color_array_2[0],color_array_2[1]],
                 'football':colors['football'] }

def animate_play(games, tracking_df, play_df, gameId, playId):
    selected_game_df = games.loc[games['gameId'] == gameId].copy()
    selected_play_df = play_df.loc[(play_df['playId'] == playId) & (play_df['gameId'] == gameId)].copy()

    tracking_players_df = tracking_df.copy()
    selected_tracking_df = tracking_players_df.loc[(tracking_players_df['playId'] == playId) & (tracking_players_df['gameId'] == gameId)].copy()

    sorted_frame_list = selected_tracking_df.frameId.unique()
    sorted_frame_list.sort()

    team_combos = list(set(selected_tracking_df['club'].unique()) - set(['football']))
    color_orders = ColorPairs(team_combos[0], team_combos[1])

    line_of_scrimmage = selected_play_df['absoluteYardlineNumber'].values[0]

    if selected_tracking_df['playDirection'].values[0] == 'right':
        first_down_marker = line_of_scrimmage + selected_play_df['yardsToGo'].values[0]
    else:
        first_down_marker = line_of_scrimmage - selected_play_df['yardsToGo'].values[0]
    
    week = games.loc[games['gameId'] == gameId, 'week'].iloc[0]
    quarter = selected_play_df['quarter'].values[0]
    gameClock = selected_play_df['gameClock'].values[0]
    playDescription = selected_play_df['playDescription'].values[0]

    if len(playDescription.split(" ")) > 15 and len(playDescription) > 115:
        playDescription = " ".join(playDescription.split(" ")[0:16]) + "<br>" + " ".join(playDescription.split(" ")[16:])

    updatemenus_dict = [
        {
            "buttons": [
                {
                    "args": [None, {"frame": {"duration": 100, "redraw": False},
                                    "fromcurrent": True, "transition": {"duration": 0}}],
                    "label": "Play",
                    "method": "animate"
                },
                {
                    "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                      "mode": "immediate",
                                      "transition": {"duration": 0}}],
                    "label": "Pause",
                    "method": "animate"
                }
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 87},
            "showactive": False,
            "type": "buttons",
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top"
        }
    ]

    sliders_dict = {
        "active": 0,
        "yanchor": "top",
        "xanchor": "left",
        "currentvalue": {
            "font": {"size": 20},
            "prefix": "Frame:",
            "visible": True,
            "xanchor": "right"
        },
        "transition": {"duration": 300, "easing": "cubic-in-out"},
        "pad": {"b": 10, "t": 50},
        "len": 0.9,
        "x": 0.1,
        "y": 0,
        "steps": []
    }

    frames = []
    for frameId in sorted_frame_list:
        data = []
        data.append(
            go.Scatter(
                x=np.arange(20, 110, 10),
                y=[5] * len(np.arange(20, 110, 10)),
                mode='text',
                text=list(map(str, list(np.arange(20, 61, 10) - 10) + list(np.arange(40, 9, -10)))),
                textfont_size=30,
                textfont_family="Courier New, monospace",
                textfont_color="#ffffff",
                showlegend=False,
                hoverinfo='none'
            )
        )
        data.append(
            go.Scatter(
                x=np.arange(20, 110, 10),
                y=[53.5 - 5] * len(np.arange(20, 110, 10)),
                mode='text',
                text=list(map(str, list(np.arange(20, 61, 10) - 10) + list(np.arange(40, 9, -10)))),
                textfont_size=30,
                textfont_family="Courier New, monospace",
                textfont_color="#ffffff",
                showlegend=False,
                hoverinfo='none'
            )
        )

        data.append(
            go.Scatter(
                x=[line_of_scrimmage, line_of_scrimmage],
                y=[0, 53.5],
                line_dash='dash',
                line_color='blue',
                showlegend=False,
                hoverinfo='none'
            )
        )

        data.append(
            go.Scatter(
                x=[first_down_marker, first_down_marker],
                y=[0, 53.5],
                line_dash='dash',
                line_color='yellow',
                showlegend=False,
                hoverinfo='none'
            )
        )

        endzoneColors = {0: color_orders[selected_game_df['homeTeamAbbr'].values[0]][0],
                         110: color_orders[selected_game_df['visitorTeamAbbr'].values[0]][0]}
        
        for x_min in [0, 110]:
            data.append(
                go.Scatter(
                    x=[x_min, x_min, x_min + 10, x_min + 10, x_min],
                    y=[0, 53.5, 53.5, 0, 0],
                    fill="toself",
                    fillcolor=endzoneColors[x_min],
                    mode="lines",
                    line=dict(
                        color="white",
                        width=3
                    ),
                    opacity=1,
                    showlegend=False,
                    hoverinfo="skip"
                )
            )

        target_nflId = 40011
        for team in selected_tracking_df['club'].unique():
            plot_df = selected_tracking_df.loc[
                (selected_tracking_df['club'] == team) & (selected_tracking_df['frameId'] == frameId)
            ].copy()

            if team != 'football':
                for nflId in plot_df['nflId'].unique():
                    selected_player_df = plot_df.loc[plot_df['nflId'] == nflId]
                    displayName = selected_player_df['displayName'].values[0]
                    s = round(selected_player_df['s'].values[0] * 2.23693629205, 3)
                    hover_text = f"nflId:{nflId}<br>displayName:{displayName}<br>Player Speed:{s} MPH"

                    if nflId == target_nflId:
                        scaled_prob = selected_player_df['scaled_prob'].values[0]
                        color = scale_colors[scaled_prob][0]
                        line_color = 'darkred'
                        size = 15
                    else:
                        color = 'grey'
                        line_color = 'black'
                        size = 10

                    data.append(go.Scatter(
                        x=selected_player_df['x'],
                        y=selected_player_df['y'],
                        mode='markers',
                        marker=go.scatter.Marker(
                            color=color,
                            line=go.scatter.marker.Line(width=2, color=line_color),
                            size=size
                        ),
                        name=f"{team} Player" if nflId != target_nflId else f"Highlighted Player",
                        hovertext=hover_text,
                        hoverinfo='text'
                    ))
            else:
                data.append(go.Scatter(
                    x=plot_df['x'],
                    y=plot_df['y'],
                    mode='markers',
                    marker=go.scatter.Marker(
                        color=color_orders[team][0],
                        line=go.scatter.marker.Line(width=2, color=color_orders[team][1]),
                        size=10
                    ),
                    name=team,
                    hoverinfo='none'
                ))

        event = selected_tracking_df.loc[selected_tracking_df['frameId'] == frameId, 'event'].values[0]
        event_text = f" ({event})" if pd.notna(event) else ""
        slider_step = {'args': [
            [frameId],
            {'frame': {'duration': 100, 'redraw': False},
             'mode': 'immediate',
             'transition': {'duration': 0}}
        ],
            'label': f"{frameId}{event_text}",
            'method': 'animate'}
        sliders_dict['steps'].append(slider_step)
        frames.append(go.Frame(data=data, name=str(frameId)))

    scale = 10
    layout = go.Layout(
        autosize=False,
        width=120 * scale,
        height=60 * scale,
        xaxis=dict(range=[0, 120], autorange=False, tickmode='array', tickvals=np.arange(10, 111, 5).tolist(), showticklabels=False),
        yaxis=dict(range=[0, 53.3], autorange=False, showgrid=False, showticklabels=False),

        plot_bgcolor='#00B140',
        title=f"GameId: {gameId}, PlayId: {playId}<br>{gameClock} {quarter}Q : Week {week}" + "<br>" * 19 + f"{playDescription}",
        updatemenus=updatemenus_dict,
        sliders=[sliders_dict]
    )

    fig = go.Figure(
        data=frames[0]['data'],
        layout=layout,
        frames=frames[1:]
    )

    for x_min in [0, 110]:
        if x_min == 0:
            angle = 270
            teamName = selected_game_df['homeTeamAbbr'].values[0]
        else:
            angle = 90
            teamName = selected_game_df['visitorTeamAbbr'].values[0]
        fig.add_annotation(
            x=x_min + 5,
            y=53.5 / 2,
            text=teamName,
            showarrow=False,
            font=dict(
                family="Courier New, monospace",
                size=32,
                color="White"
            ),
            textangle=angle
        )
    return fig

def main(gid,pid):    
    games = pd.read_csv(f'{project_dir}/games.csv')
    plays = pd.read_csv(f'{project_dir}/plays.csv')
    players = pd.read_csv(f'{project_dir}/players.csv')
    tracking_df = pd.read_csv(f'./data/tracking_example_2022110610_88.csv')
    
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
    
    tracking_df['scaled_prob'] = tracking_df['pred'].apply(scale_probability)
    tracking_df['scaled_prob'] = tracking_df['scaled_prob'].fillna(0)

    fig = animate_play( games=games, tracking_df=tracking_df, play_df=plays,
                        players=players, gameId=gid, playId=pid )
    fig.show()

if __name__ == "__main__":
    paste = "2022110610_88"
    gid, pid = map(int, paste.split('_'))

    main(gid, pid)