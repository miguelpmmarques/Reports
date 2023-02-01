import streamlit as st

from RawDataPipeline import *
from Analysis import *
from fpdf import FPDF
from datetime import datetime

from io import StringIO,BytesIO,BufferedReader



def create_report(parse_home_away,player_data,metadata,load_data=True):

    def imgToBytes(fig):
        buf = BytesIO()

        fig.savefig(buf, format='png')

        f = BufferedReader(buf)

        f.seek(0)

        return BytesIO(f.read())  
    
    def get_name_date(folder_path):
        info = folder_path.split("/")[1]
        ind = info.find(" ")
        return info[ind+1:],info[:ind]

    def create_title(pdf,game_name):
        pdf.set_font('Arial', '', 24)  
        pdf.ln(40)
        pdf.write(5, f"{game_name}")
        pdf.set_font('Arial', '', 12)
        #pdf.ln(10)
       

    def write_string(string,pdf):
        pdf.set_font('Arial', '', 12)  
        pdf.ln(5)
        string = string.replace("\n","     ")
        pdf.write(5, f"{string}")
        
    def write_string_abs_y(string,pdf,y):
        pdf.set_font('Arial', '', 12)  
        pdf.ln(5)
        pdf.write(5, f"{string}",y=7)

    WIDTH = 210
    HEIGHT = 297
    path = "Rene Weekly Report/"
    #game_name, game_date = get_name_date(folder_path)
    filename="report.pdf"



    pdf = FPDF()
    pdf.add_page()
    st.sidebar.info('Start Creating PDF File',icon="ℹ️")
    # Title
    pdf.image(path+"resources/capa.png", 0, 0, WIDTH)
    
    create_title(pdf,'{} vs {}'.format( parse_home_away['H'],parse_home_away['A'],))
    pdf.ln(10)

    # Game and Net time
    game,net = display_time(player_data["Ball"])
    pdf.ln(5)
    write_string(game,pdf)
    pdf.ln(5)
    write_string(net,pdf)
    pdf.ln(10)

    
    #Ball Possession
    fig = plot_ball_possession(player_data["Ball"][2])
    pdf.image(imgToBytes(fig),h=85,x=30)
    pdf.ln(5)

    with st.sidebar:
        with st.spinner('Loading Speed Charts 1/4'):   
            fig = analyse_team_possession(metadata,player_data)
            pdf.image(imgToBytes(fig),h=95,x=20)

    # Speed
    pdf.add_page()
    
    with st.sidebar:
        with st.spinner('Loading Speed Charts 2/4'):  

            fig = get_rene_stats(15,'FC Twente',metadata,player_data)
    pdf.image(imgToBytes(fig),h=85,x=25)#,x=30)
    pdf.ln(5)
    
    with st.sidebar:
        with st.spinner('Loading Speed Charts 3/4'):  
            fig = get_rene_stats(20,'FC Twente',metadata,player_data)
    pdf.image(imgToBytes(fig),h=85,x=25)#,x=30)
    pdf.ln(5)


    with st.sidebar:
        with st.spinner('Loading Speed Charts 4/4'):  
            fig = get_rene_stats(25,'FC Twente',metadata,player_data)
    pdf.image(imgToBytes(fig),h=85,x=25)#,x=30)
    pdf.ln(5)

    st.sidebar.success('Speed Charts Done',icon="✅")
    
    
    # Heat Maps
    print("--- Heat Maps ---")
    pdf.add_page()
    
    positions = ["Goalkeeper","Defender","Midfielder","Striker","Substitute"]

    meta_filter = metadata[metadata["StartFrameCount"]!=0]
    meta_filter = meta_filter[meta_filter["Team"] == "FC Twente"]
    st.sidebar.info('Loading Individuals Heat Maps', icon="ℹ️")
    
    curr_y = 20 
    for position in positions:
        with st.sidebar:
            with st.spinner('Loading {} Heat Maps'.format(position)):
                for p_name in list(meta_filter[meta_filter["Position"] == position].FullName):
                    
                    p = player_data[p_name][2]
                    if load_data:

                        fig1 = heatmap_player_together(p[p.Possession==True],
                                        title= "{} Time spent in each square (%) {}".format(p_name,"With Possession"),
                                        show=False
                                    ).to_image(format="png")
                    
                                    #.write_image(path+"/resources/{}With.png".format(p_name))
                        fig2 = heatmap_player_together(p[p.Possession==False],
                                        title= "{} Time spent in each square (%) {}".format(p_name,"Without Possession"),
                                        show=False
                                    ).to_image(format="png")
                    pdf.image(BytesIO(fig1),h=70,x=5,y=curr_y)
                    pdf.image(BytesIO(fig2),h=70,x=105,y=curr_y)
                    #pdf.ln(60)
                    curr_y+=70
                    if curr_y > 230:
                        pdf.add_page()
                        curr_y = 20
    st.sidebar.success('Heat Maps Done',icon="✅")

    if pdf.get_y() > 11:
        pdf.add_page()
        
    
    pdf.add_page()
    net_time = create_net_time_per_player(metadata,player_data)
    TABLE_COL_NAMES = ("Player", "Total Net Time")
    TABLE_DATA = tuple(net_time.itertuples(index=False, name=None))

    line_height = pdf.font_size * 2
    col_width = 80#pdf.epw / 4  # distribute content evenly
    

    #render_table_header()
    create_title(pdf,"Net time per player")
    pdf.ln(15)
    pdf.set_font(style='B')
    for datum in TABLE_COL_NAMES:
        
        
        pdf.cell(col_width, line_height, datum, border=0)
    pdf.set_font(style='')

    pdf.ln(line_height)
    for i,row in enumerate(TABLE_DATA):
        for j,datum in enumerate(row):
            if j==0:
                pdf.set_font(style='B')
            if i%2==0:
                pdf.set_fill_color(235,132,132)
                pdf.cell(col_width, line_height, datum, border=1,fill=True)
            else:
                pdf.cell(col_width, line_height, datum, border=1)
            
            pdf.set_font(style='')
        pdf.ln(line_height)
    
    
    
    return BytesIO(pdf.output(dest='S'))
    
    
    


st.title('Weekly Fc Twente Reports')

files_dict = {}
c1,c2 = st.columns(2)
with c1:
    st.markdown("### Opta Files")
    files_dict["F7"] = st.file_uploader("Pick the Opta F7 file",type='xml')
    files_dict["F24"] = st.file_uploader("Pick the Opta F24 file",type='xml')
with c2:
    st.markdown("### Tracab Files")
    files_dict["METADATA"] = st.file_uploader("Pick the Tracab Metadata file",type='xml')
    files_dict["DAT"] = st.file_uploader("Pick the Tracking Data file",type='dat')


if (None in files_dict.values()):
    st.sidebar.warning("Please load all files")
    
else:
    #st.write(files_dict["DAT"].name)
    #st.write(files_dict["DAT"].readlines())
    files_dict["METADATA"] = StringIO(files_dict["METADATA"].getvalue().decode("utf-8")).read()
    files_dict["F7"] = StringIO(files_dict["F7"].getvalue().decode("utf-8")).read()
    #files_dict["DAT"] = StringIO(files_dict["DAT"].getvalue().decode("utf-8")).read()
    #st.write(files_dict)
    if st.button('Generate Game Report'):
        
        st.sidebar.info('Generating your report (30 to 90 sec)', icon="ℹ️")
        with st.sidebar:
            with st.spinner('Loading Opta Data'):
                metadata,parse_home_away,tracab_meta = import_meta_data(files_dict["METADATA"],files_dict["F7"])
        st.sidebar.success('Opta Data imported',icon="✅")
        st.markdown("<h1 style='text-align: center; color: grey;'> {} vs {}</h1>".format(parse_home_away['H'],parse_home_away['A']), unsafe_allow_html=True)

        #st.markdown("## {} vs {}".format(parse_home_away['H'],parse_home_away['A']))
        #metadata

        c1,c2 = st.columns(2)
        with c1:
            st.markdown("### {} Line Up".format(parse_home_away['H']))
            st.write(metadata[metadata["Team"]==parse_home_away['H']][['FullName','JerseyNo']].reset_index(drop=True))
        with c2:
            st.markdown("### {} Line Up".format(parse_home_away['A']))
            st.write(metadata[metadata["Team"]==parse_home_away['A']][['FullName','JerseyNo']].reset_index(drop=True))
        
        #st.write(parse_home_away)
        #st.write(tracab_meta)
        if 'player_data' in st.session_state.keys():
            player_data =  st.session_state['player_data']
        else:
            with st.sidebar:
                with st.spinner('Loading Tracab Data'):
                    tracking = pass_the_tracab(files_dict["DAT"], tracab_meta, metadata, parse_home_away)
                    first_half,second_half = split_halfs(tracking,tracab_meta)
                    player_data = get_player_data(metadata,first_half,second_half)
        
            st.session_state['player_data'] = player_data

        st.sidebar.success('Tracab Data imported',icon="✅")
        
        
        report = create_report(parse_home_away,player_data,metadata,load_data=True)
        st.sidebar.success('Report Created',icon="✅")
        with st.sidebar:
            st.download_button(
                label="Download Report",
                data=report,
                file_name='Report {} vs {} {}.pdf'.format( parse_home_away['H'],
                                                        parse_home_away['A'],
                                                        datetime.today().strftime('%Y-%m-%d'),
                                                        ),
                mime='pdf',
            )
                

 

# files = get_files_from_folder(folder_path)
# print(files)
# metadata,parse_home_away,tracab_meta = import_meta_data(files["METADATA"],files["F7"])
# tracking = pass_the_tracab(files["DAT"], tracab_meta, metadata, parse_home_away)

# first_half,second_half = split_halfs(tracking,tracab_meta)
# player_data = get_player_data(metadata,first_half,second_half)


    