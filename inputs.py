### INPUTS ###

# where is the project located?
path = 'C:/Users/mfran/OneDrive/Projects/mf_traveler_20181013'
ig_username = 'mf_traveler'

# how is the project structured?
photos_folder = 'photos'
profile_folder = 'profile'
stories_folder = 'stories'
videos_folder = 'videos'
downloads_folder = 'downloads'
out_folder = 'mosaics'

# how should the output look?
grid_name = 'mosaic'
grid_extension = 'jpg'
grid_dimension = 200
grid_square = True
grid_aspect = (16,9) #(1,1), None
grid_border_scale = 0.05
grid_border_color = 'white'
grid_gif = False

# what content should be used?
check_ig = True
use_profile = True
use_stories = True
use_videos = True
video_tick = 60
remove_duplicates = True
profile_size = 0 # set to zero to not center on profile

# how refined should the process be?
trials = 6000
angle_weight = 0.2
distance_weight = 0.3

# should the intermediate steps be saved?
print_after = 1000
secondary_scale = 1/3

debugging = False