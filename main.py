### MAIN SCRIPT ###
from sorting import *
from inputs import *
import sys

print('*** OCELOT V2.0 ***\n')
start_time = timer()

# assemble folders
photos_path = '{}/{}'.format(path,photos_folder)
profile_path = '{}/{}'.format(path,profile_folder)
stories_path = '{}/{}'.format(path,stories_folder)
videos_path = '{}/{}'.format(path,videos_folder)
project_path = '{}/{}'.format(path,out_folder)
out_path = '{}/{}'.format(project_path,temp_folder)

setup_temp_folder(out_path)

display = 'save' if save_intermediate else None

# get all media
print('Looking for files...')

print(' ...checking photos',end='')
sys.stdout.flush()
folder_searches = [photos_path]
if use_profile:
    print(' + profile',end='')
    sys.stdout.flush()
    folder_searches += [stories_path]
if use_stories:
    print(' + stories',end='')
    sys.stdout.flush()
    folder_searches += [stories_path]

files = find_files(folder_searches)
library = get_pictures(files)

if use_videos:
    print(' + videos',end='')
    sys.stdout.flush()
    library_video = extract_videos(videos_path,tick=video_tick)
    library.merge_library(library_video)

print('\n ...found {} images'.format(library.size()))

# reduce to colors
print('\nAnalyzing images...')
gallery = analyze_photos(library,remove_duplicates=remove_duplicates,stories=stories_folder,videos=videos_folder)

# assemble photos
print('Setting up grid...')
grid = setup_grid(gallery,library,
                      square=grid_square,exp=grid_exp,folder=out_path,name=grid_name,extension=grid_extension,
                      secondary_scale=secondary_scale,display=display)

taut_0 = grid.get_tautness()

# seed by color
print('\nSeeding grid...')
pattern = Pattern()
corners = pattern.generate_pattern(hsv=True,hues=True,account_for_angle=True)
grid = reseed_grid(grid,corners,folder=out_path,name=grid_name,extension=grid_extension,secondary_scale=secondary_scale,display=display)
taut_1 = grid.get_tautness()
strength_0 = Grid.strength_value(taut_0,grid.size)
strength_1 = Grid.strength_value(taut_1,grid.size)
strengthening = strength_1/strength_0
print(' ...{:0.2%} to {:0.2%} strength ({:+0.1f}x improvement)'.format(strength_0,strength_1,strengthening))

# improve assembly
print('\nOptimizing grid...')
grid,n = swap_worst(grid,trials,1,folder=out_path,name=grid_name,extension=grid_extension,print_after=print_after,secondary_scale=secondary_scale,display=display)

taut_2 = grid.get_tautness()

# finish and print
print('Saving grid...')
save_name = find_next_name(out_path,grid_name,grid_extension,number=True)
finalize_grid(grid,library,out_path,save_name,extension=grid_extension,dimension=grid_dimension,
              border=int(grid_dimension*grid_border_scale),border_color=grid_border_color)

save_name = find_next_name(project_path,grid_name,[grid_extension,gif_extension],number=True)

save_gifs(out_path,project_path,save_name,extension=grid_extension,gif_extension=gif_extension,dimension=200)
open_folder(project_path)

# summarize results
end_time = timer(start_time)
print('Ran {} optimizations'.format(n))
print('Initial strength: {:0.2%}'.format(Grid.strength_value(taut_0,grid.size)))
print('Reseed strength: {:0.2%}'.format(Grid.strength_value(taut_1,grid.size)))
print('Final strength: {:0.2%}'.format(Grid.strength_value(taut_2,grid.size)))
print('Elapsed time: {} min {} sec'.format(int(end_time[1]/60),round(end_time[1]%60)))

