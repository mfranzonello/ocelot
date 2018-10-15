### METHODS FOR OPTIMIZING GRID LAYOUT ###
from common import *
from coloring import *
from media import *
from layout import *
import copy
import os

def setup_temp_folder(temp_folder):
    # create a folder to store intermediate steps
    if os.path.isdir(temp_folder):
        for fn in os.listdir(temp_folder):
            os.remove('{}/{}'.format(temp_folder,fn))
    else:
        os.makedirs(temp_folder)

def get_pictures(files):
    # find posted photos, profile pics and stories
    photos = [Photo(fn) for fn in files]
    library = Library(photos)
    return library

def extract_videos(folder,in_extensions=['mp4'],out_name='capture',out_extension='jpg',tick=30):
    # find videos and turn to photos
    files = find_files([folder],extensions=in_extensions)
    library = Library()
    for fn in files:
        video = Video(fn)
        library.add_photos(video.get_photos(tick=tick))
    return library

def analyze_photos(library,remove_duplicates=True,verbose=True,round_color=True,grey_pct=0.75,dark_pct=0.6,
                   grey_threshold=16,dark_threshold=100,round_threshold=16,dimension=50,square=True,
                   randomize=True,stories='stories',videos='videos'):
    # look at photos
    # remove duplicate photos
    # ignore grey or dark colors unless they are predominant
    # reduce photo to primary and secondary colors
    if remove_duplicates:
        purge_count = library.purge()

        if verbose & (purge_count > 0):
            print(' ...removed {} duplicate photo{}'.format(purge_count,'s' if purge_count > 1 else ''))

    gallery = Gallery.from_library(library,round_color=round_color,verbose=verbose,grey_pct=grey_pct,dark_pct=dark_pct,
                                   grey_threshold=16,dark_threshold=100,round_threshold=round_threshold,
                                   dimension=dimension,square=square,randomize=randomize,stories=stories,videos=videos)

    return gallery

def setup_grid(gallery:Gallery,library:Library,square=False,maxsize=20,exp=1,
               folder='',name='interval',extension='jpg',print_full=True,secondary_scale=None,display=False):
    # add photos grom a gallery and library to grid
    n_pics = gallery.size
    sqr = int(math.sqrt(n_pics))
    height = sqr
    width = sqr
    if not square:
        deviation_0 = n_pics - sqr**2
        for i in range(min(sqr,4)):
            for j in range(min(sqr,4)):
                deviation_1 = n_pics - (sqr - i) * (sqr + j)
                if (deviation_1 < deviation_0) & (deviation_1 > 0):
                    deviation_0 = deviation_1
                    height = sqr - i
                    width = sqr + j
        
    grid = Grid(height,width,exp=exp)
    grid.add_from_gallery(gallery)
    #rejected = n_pics - height*width

    print(' ...using {} of {} images for {}x{} grid'.format(height*width,n_pics,height,width))

    # print first
    if print_full:
        next_name = find_next_name(folder,name,extension,number=True)
        grid.save_output(folder=folder,name=next_name,extension=extension,library=library,display=display)

    # print dull
    #next_name = find_next_name(folder,name,'jpg',number=True)
    #grid.print_grid(folder,next_name,simplify=True,vibrant=False)

    # print simple
    next_name = find_next_name(folder,name,extension,number=True)
    grid.save_output(folder=folder,name=next_name,extension=extension,secondary_scale=secondary_scale,display=display)

    return grid

def reseed_grid(grid,corners,folder='',name='interval',extension='jpg',secondary_scale=None,display=False):
    # place photos in grid based on pattern
    grid = grid.reseed(corners)

    next_name = find_next_name(folder,name,extension,number=True)
    grid.save_output(folder=folder,name=next_name,extension=extension,secondary_scale=secondary_scale,display=display)

    return grid

def swap_worst(grid:Grid,n_trials=1,threshold=0,folder='',name='interval',extension='jpg',
               print_after=1000,secondary_scale=None,display=False):
    # move worst performing photos around grid to improve the coloring
    # go until exhausted
    n = 0
    exhausted = False

    taut0 = grid.get_tautness()

    pairings = grid.worst_pairings()
    try:
        while (not exhausted) & (n < n_trials):
            taut1 = grid.get_tautness()
            
            pair = 0

            move_on = False
            max_improvement = 0
            time_to_print = False
            while (not move_on) & (pair < len(pairings)) & (n < n_trials):
                n += 1
                if n%print_after == 0:
                    time_to_print = True
                print_trial(n)
                    
                grid_swap = copy.deepcopy(grid)
                cell1,strength1 = grid_swap.worst_cell(pairings[pair][0])
                cell2,strength2 = grid_swap.worst_cell(pairings[pair][1])

                grid_swap.swap_pictures([cell1],[cell2])

                improvement = grid.get_tautness() - grid_swap.get_tautness()

                if improvement > max_improvement:
                    grid_improved = copy.deepcopy(grid_swap)
                    ##strengthening = (strength1 - grid_improved.cells[cell1].strength +\
                    ##    strength2 - grid_improved.cells[cell2].strength)/(strength1 + strength2)
                    max_improvement = improvement

                if improvement > threshold:
                    grid = copy.deepcopy(grid_improved)
                    move_on = True

                if (not move_on) & (pair == len(pairings)):
                    if max_improvement > 0:
                        grid = copy.deepcopy(grid_improved)
                    else:
                        exhausted = True

                pair += 1

            taut2 = grid.get_tautness()
            if taut2 < taut1:
                print_trial(n,taut=taut1,size=grid.size)#strengthening)

            if time_to_print:
                next_name = find_next_name(folder,name,extension,number=True)
                grid.save_output(folder=folder,name=next_name,extension=extension,secondary_scale=secondary_scale,display=display)

                time_to_print = False
 
    except KeyboardInterrupt:
        pass

    next_name = find_next_name(folder,name,extension,number=True)
    if n%print_after > 0:
        grid.save_output(folder=folder,name=next_name,extension=extension,secondary_scale=secondary_scale,display=display)

    print('\n')

    return grid,n

def print_trial(n,taut=None,size=0):#strengthening
    # update on trial and result
    improve_text = ' | strength: '
    if taut is not None:#strengthening
        #strength_0 = Grid.strength_value(tauts[0],size)
        strength = Grid.strength_value(taut,size)
        #strengthening =  strength_1 - strength_0
        spaces = ' '  if strength < 1 else ''
        improvement = '{}{:0.2%}{}'.format(improve_text,strength,spaces)
    else:
        spaces = ' '*(len(improve_text)+len('100.0%'))
        improvement = ''
    print(' Trial {}{}'.format(n,improvement,spaces),end='\r')

def finalize_grid(grid,library,folder,save_name,extension='jpg',
                  dimension=200,border=0,border_color=(255,255,255)):
    # print final grid with border
    if type(border_color) is str:
        rainbow = Rainbow()
        border_color = rainbow.get_rgb(border_color,scaled=False)
        if border_color is None:
            border_color = (0,0,0)

    grid.save_output(folder=folder,name=save_name,extension=extension,library=library,dimension=dimension,
                     display='save',border=border,border_color=border_color)

def save_gifs(temp_path,folder,save_name,extension='jpg',gif_extension='gif',dimension=200,durations=[500,1000]):
    files = sorted([fn for fn in os.listdir(temp_path) if '.{}'.format(extension) in fn])
    # save intermediate steps as a gif and move out of temp folder

    if len(files) > 1:
        imgs = [Image.open('{}/{}'.format(temp_path,fn)).resize((dimension,dimension)) for fn in files]
        duration = durations[0]
        repeats = durations[1]//durations[0]
        append_images = imgs[1:-1] + [imgs[-1]]*repeats

        imgs[0].save('{}/{}.{}'.format(folder,save_name,gif_extension),save_all=True,duration=duration,append_images=append_images,loop=0)

        # delete all but final file
        for fn in files[:-1]:
            os.remove('{}/{}'.format(temp_path,fn))

    # move final file and remove temp folder
    last_file = '{}/{}'.format(temp_path,files[-1])
    move_file = '{}/{}.{}'.format(folder,save_name,extension)
    
    os.rename(last_file,move_file)

    if len(os.listdir(temp_path)) == 0:
        os.removedirs(temp_path)