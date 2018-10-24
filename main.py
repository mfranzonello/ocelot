### MAIN SCRIPT ###
from sorting import *
#from inputs import *

print('*** OCELOT V2.9 ***\n')

# assemble folders
project = Project()

# get all media
finder = Finder(project)
finder.find()

# reduce to colors
collector = Collector(finder)
collector.create_gallery(remove_duplicates=project.remove_duplicates,round_color=True,grey_pct=0.75,dark_pct=0.6,
                         grey_threshold=16,dark_threshold=100,round_threshold=16,dimension=50,aspect=project.grid_aspect,
                         randomize=True,stories=project.stories_folder,videos=project.videos_folder,
                         center=project.profile_folder if (project.use_profile & project.profile_size) else None)##,lattice=project.grid_shape)

# set up printer
printer = Printer(collector,name=project.grid_name,dimension=project.grid_dimension,
                  border_scale=project.grid_border_scale,border_color=project.grid_border_color,
                  target_aspect=project.grid_aspect if (project.grid_aspect is not None) & project.grid_aspect_force else None,
                  debugging=project.debugging)

for run in project.runs:
    # assemble photos
    assembler = Assembler(collector,printer,name=project.grid_name,aspect=project.grid_aspect,center_size=project.profile_size,
                          secondary_scale=project.secondary_scale,
                          print_gif=project.grid_gif)
    project.add_result('initial',assembler.get_strength())

    # seed by color
    sorter = Sorter(assembler,print_after=project.print_after)
    sorter.reseed()
    project.add_result('reseed',sorter.get_strength())

    # improve assembly
    sorter.swap_worst(trials=project.trials)
    sorter.finalize()
    project.add_result('iterations',sorter.n_trials)
    project.add_result('final',sorter.get_strength())

    # finish and print
    printer.finalize()

    # summarize results
    project.summarize()