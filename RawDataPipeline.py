from itertools import compress
import pandas as pd
import re
import numpy as np
import os
import streamlit as st

from socceraction.data.opta.parsers.f24_xml import F24XMLParser

import xml.etree.ElementTree as ET

#import torch
#from torch.nn.functional import softplus


from lxml import objectify


def get_files_from_folder(folder_path):
    files = os.listdir(folder_path)
    files_dict = {}
    for f in files:
        if "OptaF7" in f:
            files_dict["F7"] = folder_path+f
        elif "OptaF24" in f:
            files_dict["F24"] = folder_path+f
        elif "TracabDat" in f:
            files_dict["DAT"] = folder_path+f
        elif "TracabMetaData" in f:
            files_dict["METADATA"] = folder_path+f
    
    return files_dict

def import_meta_data(filename,positionfile):

    def parse_tracking_metadata(filename):
   
        tree = ET.ElementTree(ET.fromstring(filename))       # parse the raw xml 
        root = tree.getroot()           # get the root object to access the information 

        gamexml = root.findall('match')[0]      # get all of the nodes called 'match'

        info_raw = []       # create an empty list for storing the data 

        # for each period node get the start and end, appending them to the infa_raw list
        for i in gamexml.iter('period'):
                info_raw.append( i.get('iStartFrame') )
                info_raw.append( i.get('iEndFrame') )

        game_info = dict()      # Create empty dict for storing the information 

        # get all the information for each period and add the info to the dictionary 
        game_info['period1_start'] = int(info_raw[0])
        game_info['period1_end'] = int(info_raw[1])
        game_info['period2_start'] = int(info_raw[2])
        game_info['period2_end'] = int(info_raw[3])
        game_info['period3_start'] = int(info_raw[4])
        game_info['period3_end'] = int(info_raw[5])
        game_info['period4_start'] = int(info_raw[6])
        game_info['period4_end'] = int(info_raw[7])

        # get all the information for the pitch sizes and add the info to the dictionary 
        for detail in root.iter('match'):
            game_info['pitch_x'] = int(float(detail.get('fPitchXSizeMeters')))
            game_info['pitch_y'] = int(float(detail.get('fPitchYSizeMeters')))

        # return the dictionary of information 

        return(game_info)
    root = objectify.fromstring(filename)
    
    home = [(
     int(player.PlayerId),
     str(player.FirstName),
     str(player.LastName),
     int(player.StartFrameCount),
     int(player.EndFrameCount),
     int(player.JerseyNo),
     str(root.HomeTeam.LongName)) for player in root.HomeTeam.Players.Player]
    away = [(
     int(player.PlayerId),
     str(player.FirstName),
     str(player.LastName),
     int(player.StartFrameCount),
     int(player.EndFrameCount),
     int(player.JerseyNo),
     str(root.AwayTeam.LongName)) for player in root.AwayTeam.Players.Player]
    columns = [
        "PlayerID",
        "FirstName",
        "LastName",
        "StartFrameCount",
        "EndFrameCount",
        "JerseyNo",
        "Team",
    ]
    meta = pd.DataFrame(home+away, columns=columns)
    meta["FullName"] = meta["FirstName"]+" "+meta["LastName"]
    
    parse_home_away = {
        "H":root.HomeTeam.LongName,
        "A":root.AwayTeam.LongName,
    }
    
    xml_data = positionfile  # Read file
    root = ET.XML(xml_data)  # Parse XML
    player_position = []
    for child in root.iter():
        if child.tag == "MatchPlayer":
            if child.get("Position") == "Substitute":
                player_position.append((child.get("SubPosition"),int(child.get("PlayerRef")[1:])))
            else:
                player_position.append((child.get("Position"),int(child.get("PlayerRef")[1:])))

    players_pos = pd.DataFrame(player_position,columns=["Position","ID"])
    metadata = meta.join(players_pos.set_index('ID'), 
              on='PlayerID')
    
    return metadata,parse_home_away,parse_tracking_metadata(filename)

def pass_the_tracab(tracab_file, 
                        meta,
                        metadata,
                        parse_home_away,
                        add_distance_to_ball = False,
                        add_distance_to_goals = False):
    # 25 Hz


    print("")
    print("~--------------------------------------------~")
    print("|----           Pass the Tracab          ----|")


    ## time estimation
    
    sec_low = 10
    sec_high = 18
    
    if add_distance_to_ball: 
        sec_low = sec_low + 4
        sec_high = sec_high + 6
        
    if add_distance_to_goals: 
        sec_low = sec_low + 4
        sec_high = sec_high + 6

    print("|----   expect between " + str(sec_low) + " - " + str(sec_high) + " seconds   ----|")
    


    ## open file and store as main block of data 'content'
   
    #with open(tracab_file) as fn:
    content = tracab_file.readlines()

    ## strip the content into lines
    tdat_raw = [x.strip().decode("utf-8")  for x in content]

    ## within each line split into relevant chunks (frame, ball, humans)
    tdat_raw_n = [x.split(":")[0:3] for x in tdat_raw]

    initial_length_of_file_to_parse = len(tdat_raw_n)

    ## calculate the frameIDs
    frameID = [int(f[0]) for f in tdat_raw_n]
    
    ## work out which ones are within the playing time 
    frame_include = [(meta['period1_start'] <= f <= meta['period1_end']) or 
                     (meta['period2_start'] <= f <= meta['period2_end']) or
                     (meta['period3_start'] <= f <= meta['period3_end']) or
                     (meta['period4_start'] <= f <= meta['period4_end']) for f in frameID]

    ## remove frames that are not within the playing time to have a lighter parsing load
    frameID = list(compress(frameID, frame_include))
    tdat_raw_n = list(compress(tdat_raw_n, frame_include))

    # print a report of dropped frames 
    trimmed_length_of_file_to_parse = len(tdat_raw_n)

    print( "|----     " + str(100 - (round(trimmed_length_of_file_to_parse / initial_length_of_file_to_parse, 2) * 100)) + "% of frames discarded      ----|")

    ## Human Segment 

    humans_raw = [f[1].split(";")[:-1] for f in tdat_raw_n]

    frameID_list = []
    team = []
    target_id = []
    jersey_no = []
    x = []
    y = []
    speed = []
    
    for i in range(0,len(humans_raw)):
        for p in humans_raw[i]:
            human_parts = p.split(",")
            if human_parts[0] == '1' or human_parts[0] == '0':
                frameID_list.append(float(frameID[i]))
                if human_parts[0] == "0":
                    team.append("A")
                else:
                    team.append("H")
                #team.append(float(human_parts[0]))
                target_id.append(float(human_parts[1]))
                jersey_no.append(float(human_parts[2]))
                x.append(float(human_parts[3]))
                y.append(float(human_parts[4]))
                speed.append(float(human_parts[5]))

    tdat = pd.DataFrame(
    {'frameID': frameID_list,
     'team': team,
     'target_id': target_id,
     'jersey_no': jersey_no,
     'x': x,
     'y': y,
     'speed': speed})

    tdat['z'] = 0

    ### BALL SEGMENT 

    ball = [f[2].replace(";","").split(",") for f in tdat_raw_n]
    ball_x = [float(f[0]) for f in ball]
    ball_y = [float(f[1]) for f in ball]
    ball_z = [float(f[2]) for f in ball]
    ball_speed = [float(f[3]) for f in ball]
    ball_owning_team = [f[4] for f in ball]
    ball_status = [f[5] for f in ball]

    balldat = pd.DataFrame(
    {'frameID': frameID,
     'x': ball_x,
     'y': ball_y,
     'z': ball_z,
     'speed': ball_speed,
     'ball_owning_team': ball_owning_team,
     'ball_status': ball_status
    })

    balldat['team'] = 10
    balldat['target_id'] = 100
    balldat['jersey_no'] = 999

    ## MERGE SEGMENT 
    tdat = pd.merge(tdat, balldat[['ball_owning_team', 'ball_status', 'frameID']], on = "frameID" )

    frames = [tdat, balldat]
    tdat = pd.concat(frames, sort=True)

    ### add distance to goals 
    if add_distance_to_goals:
        tdat['dist_goal_1'] = tdat[['x', 'y']].sub(np.array([-5250,0])).pow(2).sum(1).pow(0.5).round()
        tdat['dist_goal_2'] = tdat[['x', 'y']].sub(np.array([5250,0])).pow(2).sum(1).pow(0.5).round()

    ### add distance to ball 
    if add_distance_to_ball:
        
        ball_tdat = balldat[['frameID', 'x', 'y']]
        ball_tdat.columns = ['frameID', 'ball_x', 'ball_y'] # rename to match merge 
        tdat = pd.merge(tdat, ball_tdat, how='left', on=['frameID']) #merge the ball information per frameID
        tdat['dist_2_ball'] = tdat[['x', 'y']].sub(np.array(tdat[['ball_x', 'ball_y']])).pow(2).sum(1).pow(0.5).round()
    
    tdat['match_id'] = re.sub("[^0-9]", "", tracab_file.name)
    
    tdat["x"] = tdat.x/100+52.5
    tdat["y"] = tdat.y/100+34
    tdat["Team with the ball"] = tdat['ball_owning_team'].map(parse_home_away,
                             na_action=None).astype(str)
    tdat["team"] = tdat['team'].map(parse_home_away,
                             na_action=None).astype(str)
    tdat["jersey_no"] = tdat.jersey_no.astype(int)
    tdat["speedkmh"] = tdat.speed * 3.6
    
    small_metadata = metadata[["JerseyNo","FullName","Team"]]
    tdat = pd.merge(tdat, small_metadata,  how='left', left_on=['jersey_no','team'],
                  right_on = ['JerseyNo','Team']).drop(columns=["Team","JerseyNo"])

    
    print("|----        MatchID " + re.sub("[^0-9]", "", tracab_file.name) + " Parsed       ----|")
    
    print("~--------------------------------------------~")
    print("")
    return(tdat)


def preprocess_half(half,half_id,tracab_meta):
    if half_id == 1:
        half["Period"] = 1
        half["Time [s]"] = (half.frameID-tracab_meta["period1_start"])/25
        #half["Minute"] = ((half.frameID-tracab_meta["period1_start"])/25//60).astype(int)
    if half_id == 2:
        half["Period"] = 2
        half["Time [s]"] = (half.frameID-tracab_meta["period2_start"])/25+45*60
    half["Minutes"] = (half["Time [s]"]//60).astype(int)  
    half["Seconds"] = round(np.floor(half["Time [s]"]) - half["Minutes"]*60).astype(int)
    half["resample_aux"] = (half["Time [s]"]*100).astype(int)
    #half = half[half["resample_aux"]%8 == 0]
    half["Time Text"] = half.Minutes.astype(str)+":"+half.Seconds.astype(str)

    parse_ball_status = {
        'Alive':1,
        'Dead':0,
    }

    half["DeadAliveBall"] = half['ball_status'].map(parse_ball_status,
                                 na_action=None).astype(str)
    half["Possession"]=(half["Team with the ball"] == half["team"])
    half.rename(columns = {'x':'X', 
                 'y':'Y',
                 'speed':'Snelheid',
                 'speedkmh':'Speedkmh',
                 'FullName':'Naam',
                 'jersey_no':'Shirt',
                }, 
      inplace = True)
    half = half.drop(columns=[
        "resample_aux",
        "ball_owning_team",
        "ball_status",
        "z"])
    return half

def split_halfs(tracking,tracab_meta):
    first_half = tracking[tracking["frameID"] < tracab_meta["period1_end"]]
    second_half = tracking[tracking["frameID"] > tracab_meta["period2_start"]]
    first_half = preprocess_half(first_half,1,tracab_meta)
    second_half = preprocess_half(second_half,2,tracab_meta)
    
    return first_half,second_half
    
def get_player_data(metadata,first_half,second_half):
    def update_left_to_right(player_data,metadata): 
        
        def change_other_half(player_data,half_twente,half_other,team):
            for p in player_data.keys():
                try:
                    if metadata[metadata["FullName"]==p].Team.values[0] == team:                    
                        player_data[p][half_twente]["X_l2r"] = 105 - player_data[p][half_twente].X
                        player_data[p][half_twente]["Y_l2r"] = 68 - player_data[p][half_twente].Y
                        player_data[p][half_other]["X_l2r"] = player_data[p][half_other].X
                        player_data[p][half_other]["Y_l2r"] = player_data[p][half_other].Y

                        both_halfs = player_data[p][0].append(player_data[p][1])
                        player_data[p].append(both_halfs.reset_index())
                    else:                  
                        player_data[p][half_other]["X_l2r"] = 105 - player_data[p][half_other].X
                        player_data[p][half_other]["Y_l2r"] = 68 - player_data[p][half_other].Y
                        player_data[p][half_twente]["X_l2r"] = player_data[p][half_twente].X
                        player_data[p][half_twente]["Y_l2r"] = player_data[p][half_twente].Y

                        both_halfs = player_data[p][0].append(player_data[p][1])
                        player_data[p].append(both_halfs.reset_index())
                except:
                    print(p,"Not Found")
                
            return player_data

        goal_keepers = metadata[metadata.Position == "Goalkeeper"][["FullName","Team"]]
        print("------------")
        
        print(goal_keepers)
        
        print("------------")

        t1,t2 = tuple(goal_keepers.Team.unique())
        nameTwente = goal_keepers[goal_keepers.Team == t1].FullName.values[0]
        first_half_twente = player_data[nameTwente][0].X.mean()
        
        if first_half_twente < 52.5: # midfield
            return change_other_half(player_data,1,0,t1)
        else:
            return change_other_half(player_data,0,1,t1)

    player_data = {}
    for p in metadata.FullName:
        player_data[p] = []
        player_data[p].append(first_half[first_half.Naam == p].sort_values(by="frameID").reset_index())
        player_data[p].append(second_half[second_half.Naam == p].sort_values(by="frameID").reset_index())

    player_data = update_left_to_right(player_data,metadata)

    player_data["Ball"] = []
    player_data["Ball"].append(first_half[first_half["Shirt"] == 999].sort_values(by="frameID").reset_index())
    player_data["Ball"].append(second_half[second_half["Shirt"] == 999].sort_values(by="frameID").reset_index())
    both_halfs = player_data["Ball"][0].append(player_data["Ball"][1])
    player_data["Ball"].append(both_halfs.reset_index())

    return player_data
    


def get_events(file,events_id_file,metadata):
    
    features_to_extract = [
        "game_id",
        "event_id",
        "period_id",
        "player_id",
        "team_id",
        "type_id",
        "minute",
        "second",
        "outcome",
        "start_x",
        "start_y",
        "end_x",
        "end_y",
    ]
    
    data = F24XMLParser(file)
    events = data.extract_events()
    events_df = pd.DataFrame([list(map(ev.get, features_to_extract) ) for ev in events.values()],
             columns = features_to_extract
            )
    events_id = pd.read_csv(events_id_file)
    # Join events ids
    events_df2 = events_df.join(events_id.set_index('type_id'), on='type_id').dropna()
    events_df2.player_id = events_df2.player_id.astype(int)
    # Join players name
    events_df3 = events_df2.join(metadata[["PlayerID","FullName","Position","Team"]].set_index('PlayerID'), on='player_id')

    # Preprocess position to 105x68
    # Already playing left to right!
    events_df3.start_x = round(events_df3.start_x.astype(float)/100*105,2)
    events_df3.start_y = round(events_df3.start_y.astype(float)/100*68,2)

    events_df3.end_x = round(events_df3.end_x.astype(float)/100*105,2)
    events_df3.end_y = round(events_df3.end_y.astype(float)/100*68,2)
    
    return events_df3
    
    
