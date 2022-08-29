### MAIN SCRIPT ###
from sorting import *

print('*** OCELOT V2.9 ***\n')

# assemble folders
project = Project()

# get all media
finder = Finder(project)
finder.find()

# reduce to colors
collector = Collector(finder)

center=project.profile_folder if (project.use_profile & (project.profile_size>0)) else None

collector.create_gallery(remove_duplicates=project.remove_duplicates,round_color=True,grey_pct=0.75,dark_pct=0.6,
                         grey_threshold=16,dark_threshold=100,round_threshold=16,dimension=50,aspect=project.grid_aspect,
                         randomize=True,stories=project.stories_folder,videos=project.videos_folder,
                         center=project.profile_folder if (project.use_profile & (project.profile_size>0)) else None)

# set up printer
printer = Printer(collector,name=project.grid_name,dimension=project.grid_dimension,
                  target_aspect=project.grid_aspect if (project.grid_aspect is not None) & project.grid_aspect_force else None,
                  debugging=project.debugging)

for run in project.runs:
    # assemble photos
    engine = Engine(printer)
    engine.assemble(collector)
    project.add_result('initial',engine.get_strength())

    # seed by color
    engine.reseed()
    project.add_result('reseed',engine.get_strength())

    # improve assembly
    engine.swap_worst(trials=project.trials)
    engine.finalize()
    project.add_result('iterations',engine.n_trials)
    project.add_result('final',engine.get_strength())

    # finish and print
    printer.finalize()

    # summarize results
    project.summarize()