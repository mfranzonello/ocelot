### MAIN SCRIPT ###
from sorting import *
from inputs import *

print('*** OCELOT V2.5 ***\n')

# assemble folders
project = Project(project_path = '{}/{}'.format(path,out_folder),
                  photos_path='{}/{}'.format(path,photos_folder),
                  profile_path='{}/{}'.format(path,profile_folder) if use_profile else False,
                  stories_path = '{}/{}'.format(path,stories_folder) if use_stories else False,
                  videos_path = '{}/{}'.format(path,videos_folder) if use_videos else False)

# get all media
finder = Finder(project,tick=video_tick)

# reduce to colors
collector = Collector(finder)
collector.create_gallery(remove_duplicates=remove_duplicates,round_color=True,grey_pct=0.75,dark_pct=0.6,
                         grey_threshold=16,dark_threshold=100,round_threshold=16,dimension=50,square=grid_square,
                         randomize=True,stories='stories',videos='videos')

printer = Printer(collector,name=grid_name,dimension=grid_dimension,dimension_small=50,
                  border_scale=grid_border_scale,border_color=grid_border_color,debugging=True)

# assemble photos
assembler = Assembler(collector,printer,name=grid_name,square=grid_square,secondary_scale=secondary_scale)
project.add_result('initial',assembler.get_strength())

# seed by color
sorter = Sorter(assembler,hsv=True,hues=True,account_for_angle=True)
sorter.reseed()
project.add_result('reseed',sorter.get_strength())

# improve assembly
sorter.swap_worst(trials=trials)
sorter.finalize()
project.add_result('final',sorter.get_strength())

# finish and print
printer.finalize(grid_extension)

# summarize results
project.summarize()