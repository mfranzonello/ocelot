### INPUTS ###

# where is the project located?
path = 'C:/Users/mfran/OneDrive/Projects/mf_traveler_20181013'

# how is the project structured?
photos_folder = 'photos'
profile_folder = 'profile'
stories_folder = 'stories'
videos_folder = 'videos'
out_folder = 'mosaics'

# how should the output look?
grid_name = 'mosaic'
grid_extension = 'jpg'
gif_extension = 'gif'

grid_dimension = 200
grid_square = False
grid_border_scale = 0.05
grid_border_color = 'white'

# what content should be used?
use_profile = True
use_stories = True
use_videos = True
video_tick = 60
remove_duplicates = True

# how refined should the process be?
trials = 6000
angle_weight = 0.2
distance_weight = 0.3

# should the intermediate steps be saved?
print_after = 500
secondary_scale = 1/3

debugging = False