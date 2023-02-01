from RawDataPipeline import *
from Analysis import *

import warnings
warnings.filterwarnings('ignore')

folder_path = "Last game/"

files = get_files_from_folder(folder_path)
print(files)
metadata,parse_home_away,tracab_meta = import_meta_data(files["METADATA"],files["F7"])
tracking = pass_the_tracab(files["DAT"], tracab_meta, metadata, parse_home_away)

first_half,second_half = split_halfs(tracking,tracab_meta)
player_data = get_player_data(metadata,first_half,second_half)

