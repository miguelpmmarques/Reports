import numpy as np


import plotly.express as px
import plotly.graph_objects as go

def draw_pitch_only_lines():
    x_len = 105
    y_len = 68
    
    fig = go.Figure()
    
    fig.update_xaxes(
        range=[-5,x_len+5],
        zeroline=False,
        visible=False,
    )
    
    fig.update_yaxes(
        range=[-5,y_len+5],
        zeroline=False,
        visible=False,
        scaleanchor = "x",
        scaleratio = 1,
    )
    
    
    # According to FIFA 78AB46
    
   

    fig.add_shape(type="rect",
        xref="x", yref="y",
        x0=0, y0=0,
        x1=x_len, y1=y_len,
        line=dict(
            color="white",
            width=2,
        ),
        #fillcolor='green',
        #layer = "up"
    )
    fig.add_shape(type="rect",
        xref="x", yref="y",
        x0=0, y0=y_len/2-20.15,
        x1=16.5, y1=y_len/2+20.15,
        line=dict(
            color="white",
            width=2,
        ),
        #layer = "below"

    )
    fig.add_shape(type="rect",
        xref="x", yref="y",
        x0=x_len-16.5, y0=y_len/2-20.15,
        x1=x_len, y1=y_len/2+20.15,
        line=dict(
            color="white",
            width=2,
        ),
        #layer = "below"
    )
    fig.add_shape(type="line",
        xref="x", yref="y",
        x0=x_len/2, y0=y_len,
        x1=x_len/2,y1=0,
        line=dict(
            color="white",
            width=2,
        ),
        #layer = "below"
    )
    fig.add_shape(type="circle",
        xref="x", yref="y",

        x0=x_len/2-9.15, y0=y_len/2-9.15, 
        x1=x_len/2+9.15, y1=y_len/2+9.15,
        line=dict(
            color="white",
            width=2,
        ),
        #layer = "below"
    )
    
    
    return fig

def draw_pitch(layer = "below",bg_green=False):
    x_len = 105
    y_len = 68
    
    fig = go.Figure()
    
    fig.update_xaxes(
        range=[-5,x_len+5],
        zeroline=False,
        visible=False,
    )
    if bg_green:
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='green'
        )
    else:
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='white'
        )
    
    fig.update_yaxes(
        range=[-5,y_len+5],
        zeroline=False,
        visible=False,
        scaleanchor = "x",
        scaleratio = 1,
    )
    
    # Goalies
    fig.add_shape(type="rect",
        xref="x", yref="y",
        x0=-2, y0=y_len/2-3.45,
        x1=2, y1=y_len/2+3.45,
        line=dict(
            color="white",
            width=2,
        ),
        fillcolor='green',
        layer = "below"
    )
    fig.add_shape(type="rect",
        xref="x", yref="y",
        x0=x_len+2, y0=y_len/2-3.45,
        x1=x_len-2, y1=y_len/2+3.45,
        line=dict(
            color="white",
            width=2,
        ),
        fillcolor='green',
        layer = "below"
    )
    

    fig.add_shape(type="rect",
        xref="x", yref="y",
        x0=0, y0=0,
        x1=x_len, y1=y_len,
        line=dict(
            color="white",
            width=2,
        ),
        fillcolor='green',
        layer = "below"
    )
    fig.add_shape(type="rect",
        xref="x", yref="y",
        x0=0, y0=y_len/2-16.5,
        x1=16.5, y1=y_len/2+16.5,
        line=dict(
            color="white",
            width=2,
        ),
        layer = layer

    )
    fig.add_shape(type="rect",
        xref="x", yref="y",
        x0=x_len-16.5, y0=y_len/2-16.5,
        x1=x_len, y1=y_len/2+16.5,
        line=dict(
            color="white",
            width=2,
        ),
        layer = layer
    )
    fig.add_shape(type="line",
        xref="x", yref="y",
        x0=x_len/2, y0=y_len,
        x1=x_len/2,y1=0,
        line=dict(
            color="white",
            width=2,
        ),
        layer = layer
    )
    fig.add_shape(type="circle",
        xref="x", yref="y",

        x0=x_len/2-9.15, y0=y_len/2-9.15, 
        x1=x_len/2+9.15, y1=y_len/2+9.15,
        line=dict(
            color="white",
            width=2,
        ),
        layer = layer
    )
    
    return fig


def draw_shots(goals,fails,title="Pitch"):
    x_goal,y_goal = goals
    x_fail,y_fail = fails
    data = [
        go.Scatter(x=x_fail, y=y_fail,mode='markers', name='fail',marker_color='rgba(255, 182, 193, .9)'),
        go.Scatter(x=x_goal, y=y_goal,mode='markers', name='goal',marker_color='rgba(152, 0, 0, .8)'),
    ]
    field = draw_pitch()
    fig = go.Figure(data=data, layout=field.layout)
    fig.update_traces(showlegend=True)
    fig.update_layout(title=title)
    return fig

def draw_play(play,title="Pitch"):
    play_goal,play_fail = play
    data = (
    [go.Scatter(x=p["start_x"], y=p["start_y"],
        mode='lines+markers',
        legendgroup='Play Fail',
        legendgrouptitle_text="Play Fail",
        name = "Fail",
        showlegend= True if i == len(play_fail)-1 else False,
        marker_color='rgba(255, 182, 193, .9)') for i,p in enumerate(play_fail)]
    +
    [go.Scatter(x=p["start_x"], y=p["start_y"],
        mode='lines+markers',
        legendgroup='Play Goal',
        legendgrouptitle_text="Play Goal",
        name = "Goal",
        showlegend= True if i == len(play_goal)-1 else False,
        marker_color='rgba(152, 0, 0, .8)') for i,p in enumerate(play_goal)]
    )

    field = draw_pitch()
    fig = go.Figure(data=data, layout=field.layout)
    fig.update_layout(title=title)
    return fig

def describe_results(results,subgroup_df):
    print ("{:<65} {:<15} {:<10} ".format('Subgroup', 'Total Shots',"Goals (%)" ))
    print("______________________________________________________________________________________________________________")
    unique, counts = np.unique(subgroup_df.target,return_counts=True)
    total_shot = sum(counts)
    frequency = counts/total_shot*100
    goals = counts[1]
    goals_perc = frequency[1]
    print("{:<70} {:<10} {} ({}%)".format("ORIGINAL DATASET", total_shot,goals,round(goals_perc,2)))
    print("______________________________________________________________________________________________________________")
    
    for des in results.to_descriptions():
        unique, counts = np.unique(subgroup_df[des[1].covers(subgroup_df)].target,return_counts=True)
        total_shot = sum(counts)
        frequency = counts/total_shot*100
        goals = counts[1]
        goals_perc = frequency[1]
        print("______________________________________________________________________________________________________________")
        print("{:<70} {:<10} {} ({}%)".format(str(des[1]), total_shot,goals,round(goals_perc,2)))



def goals_fails_plays(sg_shots):
    x_goal = []
    y_goal = []
    x_fail = []
    y_fail = []
    play_goal = []
    play_fail = []
    for shot in sg_shots:
        s = shot.iloc[-1]
        
        if s.result_name == "fail":
            x_fail.append(s.start_x)
            y_fail.append(s.start_y)
            play_fail.append(shot)
        else:
            x_goal.append(s.start_x)
            y_goal.append(s.start_y)
            play_goal.append(shot)
    return (x_goal,y_goal),(x_fail,y_fail),(play_goal,play_fail)


def draw_histogram2d(sg_goals,title):
    x,y = sg_goals
    field = draw_pitch(layer = "above")
    fig = go.Figure(go.Histogram2d(
            x=x,
            y=y,
            autobinx=False,
            xbins=dict(start=0, end=105, size=3),
            autobiny=False,
            ybins=dict(start=0, end=68, size=3),
        ),layout=field.layout)
    fig.update_layout(title=title)
    return fig