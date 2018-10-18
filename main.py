### MAIN SCRIPT ###
from sorting import *
from inputs import *
import sys

print('*** OCELOT V2.5 ***\n')
start_time = timer()

# assemble folders
photos_path = '{}/{}'.format(path,photos_folder)
profile_path = '{}/{}'.format(path,profile_folder)
stories_path = '{}/{}'.format(path,stories_folder)
videos_path = '{}/{}'.format(path,videos_folder)
project_path = '{}/{}'.format(path,out_folder)
temp_path = '{}/{}'.format(project_path,temp_folder)

#setup_temp_folder(out_path)

display = 'save' if save_intermediate else None

# get all media
finder = Finder(temp_folder=temp_path,pictures_folder=photos_path,
                profile_folder=profile_path,stories_folder=stories_path,videos_folder=False) #videos_path
library = finder.get_library()

# reduce to colors
#gallery = analyze_photos(library,remove_duplicates=remove_duplicates,stories=stories_folder,videos=videos_folder)
collector = Collector(library)
gallery = collector.get_gallery(remove_duplicates=False,round_color=True,grey_pct=0.75,dark_pct=0.6,
                                grey_threshold=16,dark_threshold=100,round_threshold=16,dimension=50,square=grid_square,
                                randomize=True,stories='stories',videos='videos')

# assemble photos
assembler = Assembler(gallery,square=grid_square,secondary_scale=secondary_scale)
grid = assembler.get_grid()

#grid = setup_grid(gallery,library,
#                      square=grid_square,exp=grid_exp,folder=out_path,name=grid_name,extension=grid_extension,
#                      secondary_scale=secondary_scale,display=display)

taut_0 = grid.get_tautness()

# seed by color

corners = Pattern.generate_pattern(hsv=True,hues=True,account_for_angle=True)

sorter = Sorter(grid)
sorter.reseed(corners)

##grid = reseed_grid(grid,corners,folder=out_path,name=grid_name,extension=grid_extension,secondary_scale=secondary_scale,display=display)
##taut_1 = grid.get_tautness()
##print(' ...{:0.2%} to {:0.2%} strength'.format(taut_0,taut_1))

# improve assembly
sorter.swap_worst(trials=trials)
grid = sorter.get_grid()

##grid,n = swap_worst(grid,n_trials=trials,threshold=0.0,folder=out_path,name=grid_name,
##                    extension=grid_extension,print_after=print_after,secondary_scale=secondary_scale,display=display)
##taut_2 = grid.get_tautness()

# finish and print
print('Saving grid...')

#Printer.print_grid(grid,library)
#Printer.print_gif()

save_name = find_next_name(out_path,grid_name,grid_extension,number=True)
finalize_grid(grid,library,out_path,save_name,extension=grid_extension,dimension=grid_dimension,
              border=int(grid_dimension*grid_border_scale),border_color=grid_border_color)

save_name = find_next_name(project_path,grid_name,[grid_extension,gif_extension],number=True)

save_gifs(out_path,project_path,save_name,extension=grid_extension,gif_extension=gif_extension,dimension=200)
open_folder(project_path)

# summarize results
end_time = timer(start_time)
print('Ran {} optimizations'.format(n))
print('Initial strength: {:0.2%}'.format(taut_0))
print('Reseed strength: {:0.2%}'.format(taut_1))
print('Final strength: {:0.2%}'.format(taut_2))
print('Elapsed time: {} min {} sec'.format(int(end_time[1]/60),round(end_time[1]%60)))