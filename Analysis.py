import matplotlib.pyplot as plt
import matplotlib.animation

import pandas as pd
import numpy as np

from math import atan2,cos,sin


from matplotsoccer import field
from IPython.core.display import HTML

from util import draw_pitch,draw_pitch_only_lines
import plotly.graph_objects as go




def plot_ball_possession(ball):
    def get_index(ball,t):
        try:
            ind = ball[ball["Time Text"] == t].index[-1]
            return ind
        except:
            return None
    ball = ball[ball.DeadAliveBall== "1"].drop(columns=["level_0"])
    ball = ball.reset_index()
    possession = ball[["Time [s]","Period","Team with the ball"]]
    teams = possession["Team with the ball"].unique()
    if teams[0] != "FC Twente":
        teams = ["FC Twente",teams[0]]
    p = [[0,0]]
    for t in possession["Team with the ball"]:
        if t == teams[0]:
            p.append([p[-1][0]+1,p[-1][1]])
        else:
            p.append([p[-1][0],p[-1][1]+1])
    poss = list(map(lambda x: [round(x[0]/sum(x)*100),round(x[1]/sum(x)*100)] ,p[1:]))
    
    team1 = np.array(poss)[:,0]
    team2 = np.array(poss)[:,1]
    
    
    time_trial = [
        0,
        15,
        30,
        45,
        60,
        75,
    ]
    
    time = []
    time_index = []
    
    for t in time_trial:
        flag = True
        while flag:
            ts = str(t)+":0"
            ind = get_index(ball,ts)
            if ind != None:
                flag = False
                time.append(ts)
                time_index.append(ind)
            else:
                t+=1
    
    time[0] = "1st Half"
    time[3] = "2nd Half"
    time.append("End Match")
    time_index.append(len(ball))
    x = np.linspace(0,len(poss)-1,len(poss))

    fig = plt.figure()
    plt.plot(x, team1, label = teams[0],c="firebrick")
    plt.plot(x, team2, label = teams[1],c="royalblue")
    plt.xticks(time_index, time)
    plt.legend()
    plt.grid()
    plt.xlabel("Time (Minutes:Seconds)")
    plt.ylabel("Ball Possession %")
    plt.title("{} {}% vs {}% {}".format(teams[0],team1[-1],team2[-1],teams[1]))
    plt.show()
    return fig 


def create_net_time_per_player(metadata,player_data):
    player_net = pd.DataFrame(columns=['Minutes_1st_half',
                                       'Seconds_1st_half',
                                       'Minutes_second_half',
                                       'Seconds_second_half',
                                       'Minutes_total',
                                       'Seconds_total'])



    meta_filter = metadata[metadata["StartFrameCount"]!=0]
    meta_filter = meta_filter[meta_filter["Team"] == "FC Twente"]

    for p_name in list(meta_filter.FullName):
        net_time = get_game_time(player_data[p_name],dead_ball_filter = True)
        player_net = player_net.append(net_time, ignore_index=True)

    player_net = player_net.astype(int)
    player_net.index = list(meta_filter.FullName)
    
    player_net = player_net[["Minutes_total","Seconds_total"]]
    player_net["Hours_total"] = player_net["Minutes_total"]//60
    player_net["Minutes_total"] = player_net["Minutes_total"]%60
    player_net = player_net.astype(str)
    player_net["Total_time"]  = player_net["Hours_total"]+":"+player_net["Minutes_total"]+":"+player_net["Seconds_total"]
    player_net['Total Net Time'] = pd.to_datetime(player_net['Total_time'], format='%H:%M:%S').dt.strftime('%H:%M:%S')
    player_net["Player"] = list(player_net.index)
    return player_net[["Player","Total Net Time"]]


def get_rene_stats(speed,team,metadata,player_data):    
    away_speed = get_distance_ball_possession_speed(metadata[metadata["Team"] == team].FullName,player_data,speed)
    away_speed.index = away_speed.Name
    #display(HTML('<h3>{}</h3>'.format(team)))
    
    fig = away_speed.plot.barh(figsize=(14,7),color={"Without Ball Possession": "red", "With Ball Possession": "green"})
    plt.xlabel("Distance Covered (m)")
    plt.title("Distance Covered with and without ball possession and with speed above {} km/h".format(speed))
    plt.grid()
    #plt.savefig(path+"/ball_poss_speed{}.png".format(speed))
   
    plt.show()
    return fig.get_figure()
    
    
def get_distance_ball_possession_speed(players,player_data,speed,filter_dead_ball=True):
        data = []
        for player in players:
            if player != "Ball":
                try:
                    tracking_data = player_data[player][0].append(player_data[player][1])
                except:
                    print(player,"not found")
                    continue
                tracking_data["X_next"] = np.append(np.array(tracking_data.X[1:]),np.nan)
                tracking_data["Y_next"] = np.append(np.array(tracking_data.Y[1:]),np.nan)
                tracking_data = tracking_data.dropna()
                
            
                tracking_data["Distance"] = np.sqrt((tracking_data.X_next-tracking_data.X)**2 +
                                            (tracking_data.Y_next-tracking_data.Y)**2)
                
                tracking_data["Snelheid_kmh"] =  tracking_data.Snelheid * 3.6
                
                #print(tracking_data.DeadAliveBall.unique())
                if filter_dead_ball:
                    tracking_data = tracking_data[tracking_data["DeadAliveBall"]=="1"]
                
                withBall_st1 = tracking_data[(tracking_data["Possession"]== True)&(tracking_data["Snelheid_kmh"]>speed)]
                withOutBall_st1 = tracking_data[(tracking_data["Possession"]== False)&(tracking_data["Snelheid_kmh"]>speed)]
                
                if sum(withBall_st1.Distance) > 0 and sum(withOutBall_st1.Distance):
                    data.append([
                        player, 
                        sum(withBall_st1.Distance),
                        sum(withOutBall_st1.Distance),
                    ])

        return pd.DataFrame(data,columns = ["Name",
                                            "With Ball Possession",
                                            "Without Ball Possession",
                                        ])

def analyse_team_possession(metadata,player_data):
    
    def get_data(metadata,player_data):
        data_rene = {}
        #data_rene["Team"] = []

        speeds = [0,15,20,25]
        teams = metadata.Team.unique()
        if teams[0] != "FC Twente":
            teams = ["FC Twente",teams[0]]

        data_rene["Speed threshold"] = []
        data_rene["{} With Ball Possession".format(teams[0])] = []
        data_rene["{} Without Ball Possession".format(teams[0])] = []
        data_rene["{} With Ball Possession".format(teams[1])] = []
        data_rene["{} Without Ball Possession".format(teams[1])] = []
        for team in teams:
            for speed in speeds:

                data = get_distance_ball_possession_speed(metadata[metadata["Team"] == team].FullName,player_data,speed).sum()
                #data_rene["Team"].append("{} speed > {} km/h".format(team,speed))
                #data_rene["Speed threshold"].append(speed)
                data_rene["{} With Ball Possession".format(team)].append(round(data["With Ball Possession"]/1000,1))
                data_rene["{} Without Ball Possession".format(team)].append(round(data["Without Ball Possession"]/1000,1))
                data_rene["Speed threshold"].append("Distance above {} km/h".format(speed))

        data_rene["Speed threshold"][0] = "Total Distance"
        data_rene["Speed threshold"] = data_rene["Speed threshold"][:4]
        data_rene = pd.DataFrame(data_rene)
        data_rene.index = data_rene["Speed threshold"]
        return data_rene

    data_rene = get_data(metadata,player_data)
    
    f, ((ax1,ax2),(ax3,ax4)) = plt.subplots(2, 2, sharey=True,figsize=(10,7))
    subplots = [ax1,ax2,ax3,ax4]
    f.tight_layout(h_pad=4)

    for i in range(data_rene.shape[0]):
        data = pd.DataFrame(data_rene.iloc[i]).to_dict()
        title = list(data.keys())[0]
        data = data[title]
        names = list(data.keys())
        names[3],names[2] = names[2],names[3]

        values = list(data.values())
        values[3],values[2] = values[2],values[3]

        ax = subplots[i].barh(range(len(data)-1), 
                 values[1:], 
                 tick_label=names[1:],
                 color= ["firebrick","royalblue","firebrick","royalblue"],
                )
                
        for p in ax:
            subplots[i].annotate(str(p.get_width()), (p.get_width() * 1.005, p.get_y()+0.3))

        subplots[i].set_xlabel("Distance (km)")
        subplots[i].set_title(title)

    plt.show() 
    return f

def get_game_time(ball,dead_ball_filter = False):
    if dead_ball_filter:
        ball_first = ball[0][ball[0]["DeadAliveBall"] == "1"]
        ball_second = ball[1][ball[1]["DeadAliveBall"] == "1"]
        ball_total = ball[2][ball[2]["DeadAliveBall"] == "1"]
    else:
        ball_first = ball[0]
        ball_second = ball[1]
        ball_total = ball[2]
    d = {}
    d["Minutes_1st_half"] = round(ball_first.shape[0]/25//60)
    d["Seconds_1st_half"] = round(ball_first.shape[0]/25 - ball_first.shape[0]/25//60*60)

    d["Minutes_second_half"] = round(ball_second.shape[0]/25//60)
    d["Seconds_second_half"] = round(ball_second.shape[0]/25 - ball_second.shape[0]/25//60*60)

    d["Minutes_total"] = round(ball_total.shape[0]/25//60)
    d["Seconds_total"] = round(ball_total.shape[0]/25 - ball_total.shape[0]/25//60*60)

    if d["Seconds_1st_half"] < 10:
        d["Seconds_1st_half"] = "0"+str(d["Seconds_1st_half"])
    if d["Seconds_second_half"] < 10:
        d["Seconds_second_half"] = "0"+str(d["Seconds_second_half"])
    if d["Seconds_total"] < 10:
        d["Seconds_total"] = "0"+str(d["Seconds_total"])

    return d

def display_time(ball):
    no_filter = get_game_time(ball,dead_ball_filter = False)
    with_filter = get_game_time(ball,dead_ball_filter = True)
    
    return ("""GAME DURATON   First Half - {}:{}    Second Half - {}:{}    Both Halves - {}:{}""".format(
        no_filter["Minutes_1st_half"],
        no_filter["Seconds_1st_half"],
        no_filter["Minutes_second_half"],
        no_filter["Seconds_second_half"],
        no_filter["Minutes_total"],
        no_filter["Seconds_total"],
        
    )),    ("""NET DURATON    First Half - {}:{}    Second Half - {}:{}    Both Halves - {}:{}""".format(
        with_filter["Minutes_1st_half"],
        with_filter["Seconds_1st_half"],
        with_filter["Minutes_second_half"],
        with_filter["Seconds_second_half"],
        with_filter["Minutes_total"],
        with_filter["Seconds_total"],
    ))



def heatmap_player_together(data,title,show=True):
        field = draw_pitch_only_lines()
        fig = go.Figure(go.Histogram2d(
                x=data.X_l2r,
                y=data.Y_l2r,
                #hoverinfo = "z",
                histnorm = "percent",
                hovertemplate = "%{z:.2f}% of the time<extra></extra>",
            autobinx=False,
                xbins=dict(start=0, end=105, size=5),
                autobiny=False,
                ybins=dict(start=0, end=68, size=4),
            colorscale=[[0, 'rgb(12,51,131)'], [0.25, 'rgb(10,136,186)'], 
            [0.5, 'rgb(242,211,56)'], [0.75, 'rgb(242,143,56)'], [1, 'rgb(217,30,30)']]
            ),layout=field.layout)
        fig.add_annotation(
            xref="x domain",
            yref="y",
            x=0.75,
            y=-3,
            text="Playing Left to Right",
            # If axref is exactly the same as xref, then the text's position is
            # absolute and specified in the same coordinates as xref.
            axref="x domain",
            # The same is the case for yref and ayref, but here the coordinates are data
            # coordinates
            ayref="y",
            ax=0.3,
            ay=-3,
            arrowhead=5,
        )
        fig.update_layout(title=title,)
        if show:
            fig.show()
        return fig



def show_tracking_position(dataset,colorscale,title="",show=True):
    try:
        change_index = dataset.index[1:][dataset.index[1:] != (dataset.index+1)[:-1]]
        change_index = [dataset.index[0]]+list(change_index)
    except: 
        field = draw_pitch()
        fig = go.Figure(data=go.Scatter(x=dataset['X_l2r'],
                                        y=dataset['Y_l2r'],
                                        mode='markers',
                                        marker_color=dataset['Speedkmh'],
                                        text=["Time - {} Speed - {}".format(time,speed) for time,speed in zip(dataset['Time Text'],dataset['Speedkmh'])],
                                        name="",
                                        hovertemplate = '%{text}<extra></extra>',
                                        marker=dict(
                                            size=3,
                                            colorscale=colorscale,
                                            showscale=True,
                                            
                                            )
                                        ),layout=field.layout)
        fig.update_layout(title=title,
        legend_title="Speed in km/h",
        )
        fig.add_annotation(
            xref="x domain",
            yref="y",
            x=0.75,
            y=-3,
            text="Playing Left to Right",
            # If axref is exactly the same as xref, then the text's position is
            # absolute and specified in the same coordinates as xref.
            axref="x domain",
            # The same is the case for yref and ayref, but here the coordinates are data
            # coordinates
            ayref="y",
            ax=0.3,
            ay=-3,
            arrowhead=5,
        )
        if show:
            fig.show()
        return fig

    field = draw_pitch()
    fig = go.Figure(data=go.Scatter(x=dataset['X_l2r'],
                                    y=dataset['Y_l2r'],
                                    mode='markers',
                                    marker_color=dataset['Speedkmh'],
                                    text=["Time - {} Speed - {}".format(time,speed) for time,speed in zip(dataset['Time Text'],dataset['Speedkmh'])],
                                    name="",
                                    hovertemplate = '%{text}<extra></extra>',
                                    marker=dict(
                                        size=3,
                                        colorscale=colorscale,
                                        showscale=True,
                                        
                                        )
                                    ),layout=field.layout)
    fig.update_layout(title=title,
    legend_title="Speed in km/h",
    )
    fig.add_trace(go.Scatter(x=dataset.loc[change_index].X_l2r, 
                             y=dataset.loc[change_index].Y_l2r,
                             mode='markers',
                             marker_color = "black",
                             name="Starting Point"

                            ))
    fig.update_layout(legend=dict(
        orientation="v",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=1
    ))
    fig.add_annotation(
            xref="x domain",
            yref="y",
            x=0.75,
            y=-3,
            text="Playing Left to Right",
            # If axref is exactly the same as xref, then the text's position is
            # absolute and specified in the same coordinates as xref.
            axref="x domain",
            # The same is the case for yref and ayref, but here the coordinates are data
            # coordinates
            ayref="y",
            ax=0.3,
            ay=-3,
            arrowhead=5,
        )
    if show:
        fig.show()
    return fig
        
# To Do:
# - Position of everything in a certain game time

def plotPosition(timestamp,metadata,player_data,frequency,seconds_window):
    
    def get_players_team(team_name,metadata,ind):
        players_team = metadata[metadata.Team == team_name].FullName
        players_team_pos = []
        
        for pA in players_team:
            try:
                #display(player_data[pA][2].iloc[ind])
                #print(ind)
                #display(player_data[pA])
                
                tracking = player_data[pA].iloc[ind]
                tracking_1 = player_data[pA].iloc[ind+1]
                
                x1,y1 = tracking.X,tracking.Y
                x2,y2 = tracking_1.X,tracking_1.Y
                
                angle = atan2((y2-y1),(x2-x1))
                
                new_x = x1 + tracking.Snelheid*cos(angle)
                new_y = y1 + tracking.Snelheid*sin(angle)
                            
                players_team_pos.append((tracking.Naam,tracking.X,tracking.Y,round(tracking.Speedkmh,2),new_x,new_y))
            except:
                #print(e)
                pass
            
        return pd.DataFrame(players_team_pos,columns=["Name","X","Y","Speedkmh","X1","Y1"]).dropna()
    
    teamA, teamB = tuple(metadata.Team.unique()) 
    players_teamA = metadata[metadata.Team == teamA].FullName
    players_teamB = metadata[metadata.Team == teamB].FullName
    
    ball = player_data["Ball"]
    
    tracking_on_time = ball[ball["Time Text"] == timestamp]
    end = tracking_on_time.index[0]
    start = end - seconds_window*frequency
    frames = []
    
    
    for t in range(start,end+1):

        teamA_pos = get_players_team(teamA,metadata,t)
        teamB_pos = get_players_team(teamB,metadata,t)
        
        
        ball_on_time = ball.iloc[t]
        
        
        data = [go.Scatter(x = teamA_pos.X, 
                             y = teamA_pos.Y,
                             mode = 'markers',
                             marker_color = "red",
                             text = ['{} <br>Speed: {} km/h'.format(n,s) for n,s in zip(teamA_pos.Name,teamA_pos.Speedkmh)],
                             hovertemplate = '%{text}',
                             name = teamA,
                            ),
                
                go.Scatter(x=teamB_pos.X, 
                             y=teamB_pos.Y,
                             mode='markers',
                             marker_color = "blue",
                             text = ['{} <br>Speed: {} km/h'.format(n,s) for n,s in zip(teamB_pos.Name,teamB_pos.Speedkmh)],
                             hovertemplate = '%{text}',
                             name=teamB,
                            ),
                go.Scatter(x=[ball_on_time.X.mean()], 
                             y=[ball_on_time.Y.mean()],
                             mode='markers',
                             marker_color = "white",
                             name="Ball",
                            )  
        ]
        
        data.extend([go.Scatter(x=[row.X,row.X1],
                             y=[row.Y,row.Y1],
                             mode='lines',
                             marker_color = "rgba(255,0,0,0.5)",
                             
                             showlegend = False,
                            ) for ind,row in teamA_pos.iterrows()])
        data.extend([go.Scatter(x=[row.X,row.X1],
                             y=[row.Y,row.Y1],
                             mode='lines',
                             marker_color = "rgba(0,0,255,0.5)",
                             
                             showlegend = False,
                            ) for ind,row in teamB_pos.iterrows()])
        
       
        frames.append(go.Frame(data = data))
          
    pitch = draw_pitch()
    fig = go.Figure(
        data=frames[0].data,
        layout=pitch.layout,
        
        frames=frames
    )
    
    fig.update_layout(
        
        updatemenus=[dict(
            type="buttons",
            buttons=[dict(label="Play",
                          method="animate",
                          args=[None, {"frame": {"duration": 10, "redraw": True},
                                "fromcurrent": True, "transition": {"duration": 1,
                                                                    "easing": "quadratic-in-out"}}],
                         
                         )])]
    )
    return fig

def plotPosition_all(metadata,player_data):
    
    def get_players_team(team_name,metadata,ind):
        players_team = metadata[metadata.Team == team_name].FullName
        players_team_pos = []
        
        for pA in players_team:
            try:
                #display(player_data[pA][2].iloc[ind])
                #print(ind)
                #display(player_data[pA])
                
                tracking = player_data[pA].iloc[ind]
                tracking_1 = player_data[pA].iloc[ind+1]
                
                x1,y1 = tracking.X,tracking.Y
                x2,y2 = tracking_1.X,tracking_1.Y
                
                angle = atan2((y2-y1),(x2-x1))
                
                new_x = x1 + tracking.Snelheid*cos(angle)
                new_y = y1 + tracking.Snelheid*sin(angle)
                            
                players_team_pos.append((tracking.Naam,tracking.X,tracking.Y,round(tracking.Speedkmh,2),new_x,new_y))
            except:
                #print(e)
                pass
            
        return pd.DataFrame(players_team_pos,columns=["Name","X","Y","Speedkmh","X1","Y1"]).dropna()
    
    teamA, teamB = tuple(metadata.Team.unique()) 
    players_teamA = metadata[metadata.Team == teamA].FullName
    players_teamB = metadata[metadata.Team == teamB].FullName
    
    ball = player_data["Ball"]
    end = list(ball.index)[-1]
    start = list(ball.index)[0]
    frames = []
    
    
    for t in range(start,end+1):

        teamA_pos = get_players_team(teamA,metadata,t)
        teamB_pos = get_players_team(teamB,metadata,t)
        
        
        ball_on_time = ball.iloc[t]
        
        
        data = [go.Scatter(x = teamA_pos.X, 
                             y = teamA_pos.Y,
                             mode = 'markers',
                             marker_color = "red",
                             text = ['{} <br>Speed: {} km/h'.format(n,s) for n,s in zip(teamA_pos.Name,teamA_pos.Speedkmh)],
                             hovertemplate = '%{text}',
                             name = teamA,
                            ),
                
                go.Scatter(x=teamB_pos.X, 
                             y=teamB_pos.Y,
                             mode='markers',
                             marker_color = "blue",
                             text = ['{} <br>Speed: {} km/h'.format(n,s) for n,s in zip(teamB_pos.Name,teamB_pos.Speedkmh)],
                             hovertemplate = '%{text}',
                             name=teamB,
                            ),
                go.Scatter(x=[ball_on_time.X.mean()], 
                             y=[ball_on_time.Y.mean()],
                             mode='markers',
                             marker_color = "white",
                             name="Ball",
                            )  
        ]
        
        data.extend([go.Scatter(x=[row.X,row.X1],
                             y=[row.Y,row.Y1],
                             mode='lines',
                             marker_color = "rgba(255,0,0,0.5)",
                             
                             showlegend = False,
                            ) for ind,row in teamA_pos.iterrows()])
        data.extend([go.Scatter(x=[row.X,row.X1],
                             y=[row.Y,row.Y1],
                             mode='lines',
                             marker_color = "rgba(0,0,255,0.5)",
                             
                             showlegend = False,
                            ) for ind,row in teamB_pos.iterrows()])
        
       
        frames.append(go.Frame(data = data))
          
    pitch = draw_pitch()
    fig = go.Figure(
        data=frames[0].data,
        layout=pitch.layout,
        
        frames=frames
    )
    
    fig.update_layout(
        
        updatemenus=[dict(
            type="buttons",
            buttons=[dict(label="Play",
                          method="animate",
                          args=[None, {"frame": {"duration": 10, "redraw": True},
                                "fromcurrent": True, "transition": {"duration": 1,
                                                                    "easing": "quadratic-in-out"}}],
                         
                         )])]
    )
    return fig



def plot_pitch_control(ball_pos,home_pos,away_pos,pc,n_frames,filename):
    
    def update(i):
        fr = i + first_frame_to_plot
        for tp in p[0].collections:
            tp.remove()
        p[0] = ax.contourf(xx,
                        yy,
                        pc[fr].t().cpu(),
                        extent = (0,105,0,68),
                        levels = np.linspace(0,1,100),
                        cmap = 'coolwarm',
                        extend='both')
        ball_points.set_offsets(np.c_[[locs_ball_reduced[i,0]],[locs_ball_reduced[i,1]]])
        ball_points2.set_offsets(np.c_[[locs_ball_reduced[i,0]],[locs_ball_reduced[i,1]]])
        home_points.set_offsets(np.c_[locs_home_reduced[:,i,0],locs_home_reduced[:,i,1]])
        away_points.set_offsets(np.c_[locs_away_reduced[:,i,0],locs_away_reduced[:,i,1]])
        return p[0].collections + [ball_points,home_points,away_points]

    
    ## use these parameters to set which frames you want to see
    first_frame_to_plot = 0
    first_frame = 0
    n_frames_to_plot = n_frames
    n_grid_points_x = 50
    n_grid_points_y = 30

    xx = np.linspace(0,105,n_grid_points_x)
    yy = np.linspace(0,68,n_grid_points_y)

    locs_ball_reduced = ball_pos[0,first_frame:(first_frame + n_frames),0,0,:]
    locs_home_reduced = home_pos[:,first_frame:(first_frame + n_frames),0,0,:]
    locs_away_reduced = away_pos[:,first_frame:(first_frame + n_frames),0,0,:]

    fig, ax=plt.subplots()
    field(ax=ax,show = False)
    ax.set_xlim(0,105)
    ax.set_ylim(0,68)
    ball_points = ax.scatter(locs_ball_reduced[first_frame_to_plot,0],
                             locs_ball_reduced[first_frame_to_plot,1],color = 'black',zorder = 15, s = 16)
    ball_points2 = ax.scatter(locs_ball_reduced[first_frame_to_plot,0],
                              locs_ball_reduced[first_frame_to_plot,1],color = 'white',zorder = 15, s = 9)
    home_points = ax.scatter(locs_home_reduced[:,first_frame_to_plot,0],
                             locs_home_reduced[:,first_frame_to_plot,1],color = 'red',zorder = 10)
    away_points = ax.scatter(locs_away_reduced[:,first_frame_to_plot,0],
                             locs_away_reduced[:,first_frame_to_plot,1],color = 'blue',zorder = 10)
    p = [ax.contourf(xx,
                     yy,
                     pc[first_frame_to_plot].t().cpu(),
                     extent = (0,105,0,68),
                     levels = np.linspace(0,1,100),
                     cmap = 'coolwarm',
                     extend='both')]
    ani = matplotlib.animation.FuncAnimation(fig, update, frames=n_frames_to_plot, 
                                         interval=40, blit=True, repeat=True)
    #plt.show()
    ani.save("{}.gif".format(filename))
    