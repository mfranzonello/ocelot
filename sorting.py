### METHODS FOR OPTIMIZING GRID LAYOUT ###
from common import *
from coloring import *
from media import *
from layout import *
import copy
import os
import sys

class Paths:
    def __init__(self,project_folder,temp_folder,pictures_folder,profile_folder=False,stories_folder=False,videos_folder=False):
        return

class Finder:
    def __init__(self,temp_folder,pictures_folder,profile_folder=False,stories_folder=False,videos_folder=False):
        self.temp_folder = temp_folder
        self.pictures_folder = pictures_folder
        self.profile_folder = profile_folder
        self.stories_folder = stories_folder
        self.videos_folder = videos_folder
        self.library = Library()

        print('Looking for files...')
        self._setup_temp_folder()
        self._get_pictures()
        if profile_folder:
            self._get_profile()
        if stories_folder:
            self._get_stories()
        if videos_folder:
            self._get_videos()

    def _setup_temp_folder(self):
        # create a folder to store intermediate steps
        if os.path.isdir(self.temp_folder):
            for fn in os.listdir(self.temp_folder):
                os.remove('{}/{}'.format(self.temp_folder,fn))
        else:
            os.makedirs(self.temp_folder)

    def _get_photos(self,folder,in_extensions=['jpg','png','bmp','gif']):
        # find posted photos, profile or stories
        files = find_files(folder,extensions=in_extensions)
        photos = [Photo(fn) for fn in files]
        library = Library(photos)
        self.library.merge_library(library)
        
    def _get_pictures(self):
        # find posted photos
        print(' ...checking photos',end='')
        sys.stdout.flush()
        self._get_photos(self.pictures_folder)
        
    def _get_profile(self):
        # find profile pic
        print(' + profile',end='')
        sys.stdout.flush()
        self._get_photos(self.profile_folder)
        
    def _get_stories(self):
        # find stories
        print(' + stories',end='')
        sys.stdout.flush()
        self._get_photos(self.stories_folder)
        
    def _get_videos(self,in_extensions=['mp4'],tick=30):
        # find videos and turn to photos
        print(' + videos',end='')
        sys.stdout.flush()
        files = find_files(self.videos_folder,extensions=in_extensions)
        library = Library()
        for fn in files:
            video = Video(fn)
            library.add_photos(video.get_photos(tick=tick))
        self.library.merge_library(library)

    def get_library(self):
        print('\n ...found {} images'.format(self.library.size()))
        return self.library

class Collector:
    def __init__(self,library):
        self.library = library
        print('\nAnalyzing images...')

    def _remove_duplicates(self):
        library = self.library
        purge_count = library.purge()
        if purge_count > 0:
            print(' ...removed {} duplicate photo{}'.format(purge_count,'s' if purge_count > 1 else ''))
        return library

    def get_gallery(self,remove_duplicates=True,round_color=True,grey_pct=0.75,dark_pct=0.6,
                    grey_threshold=16,dark_threshold=100,round_threshold=16,dimension=50,square=True,
                    randomize=True,stories='stories',videos='videos'):
        
        if remove_duplicates:
            library = self._remove_duplicates()
        else:
            library = self.library

        gallery = Gallery.from_library(library,round_color=round_color,grey_pct=grey_pct,dark_pct=dark_pct,
                                       grey_threshold=grey_threshold,dark_threshold=dark_threshold,round_threshold=round_threshold,
                                       dimension=dimension,square=square,randomize=randomize,stories=stories,videos=videos)

        return gallery

class Assembler:
    def __init__(self,gallery:Gallery,square=False,secondary_scale=None):
        height,width = self._best_fit(gallery.size,square)
        self.grid = Grid(height,width)
        self.grid.add_from_gallery(gallery)
        print('Setting up grid...')

    def _best_fit(self,n_pics,square=False):
        height = width = int(math.sqrt(n_pics))
        if not square:
            sqr = round(math.sqrt(n_pics))
            sqr_dn = round(math.sqrt(n_pics)*(1-0.1))
            sqr_up = round(math.sqrt(n_pics)*(1+0.1))

            sizes = list(itertools.product(range(sqr_dn,sqr+1),range(sqr,sqr_up+1)))
            deviations = [n_pics-i*j for i,j in sizes]
            if len(deviations)>0:
                height,width = sizes[deviations.index(min([d for d in deviations if d>=0]))]
        return height,width

    def get_grid(self):
        grid = self.grid
        return self.grid

#def setup_grid(gallery:Gallery,library:Library,square=False,maxsize=20,exp=1,
#               folder='',name='interval',extension='jpg',print_full=True,secondary_scale=None,display=False):
#    # add photos grom a gallery and library to grid
#    n_pics = gallery.size

#    height = width = int(math.sqrt(n_pics))
#    if not square:
#        sqr = round(math.sqrt(n_pics))
#        sqr_dn = round(math.sqrt(n_pics)*(1-0.1))
#        sqr_up = round(math.sqrt(n_pics)*(1+0.1))

#        sizes = list(itertools.product(range(sqr_dn,sqr+1),range(sqr,sqr_up+1)))
#        deviations = [n_pics-i*j for i,j in sizes]
#        if len(deviations)>0:
#            height,width = sizes[deviations.index(min([d for d in deviations if d>=0]))]
      
#    grid = Grid(height,width,exp=exp)
#    grid.add_from_gallery(gallery)

#    print(' ...using {} of {} images for {}x{} grid'.format(height*width,n_pics,height,width))

#    # print first
#    if print_full:
#        next_name = find_next_name(folder,name,extension,number=True)
#        grid.save_output(folder=folder,name=next_name,extension=extension,library=library,display=display)

#    # print dull
#    #next_name = find_next_name(folder,name,'jpg',number=True)
#    #grid.print_grid(folder,next_name,simplify=True,vibrant=False)

#    # print simple
#    next_name = find_next_name(folder,name,extension,number=True)
#    grid.save_output(folder=folder,name=next_name,extension=extension,secondary_scale=secondary_scale,
#                     display=display,print_strength=True)

#    return grid

#def reseed_grid(grid,corners,folder='',name='interval',extension='jpg',secondary_scale=None,display=False):
#    # place photos in grid based on pattern
#    grid = grid.reseed(corners)
#
#    next_name = find_next_name(folder,name,extension,number=True)
#    grid.save_output(folder=folder,name=next_name,extension=extension,secondary_scale=secondary_scale,
#                     display=display,print_strength=True)
#
#    return grid

class Sorter:
    def __init__(self,grid:Grid):
        self.grid = grid

    def get_strength(self):
        strength = self.grid.get_tautness()
        return strength

    def get_grid(self):
        grid = self.grid
        return grid

    def reseed(self,corners):
        print('\nSeeding grid...')
        taut_0 = self.grid.get_tautness()
        grid = self.grid.reseed(corners)
        self.grid = grid
        taut_1 = self.grid.get_tautness()
        print(' ...{:0.2%} to {:0.2%} strength'.format(taut_0,taut_1))
        return self.grid

    def swap_worst(self,threshold=0,trials=1):
        print('\nOptimizing grid...')
        n = 0
        swaps = 0
        exhausted = False
        taut_0 = self.grid.get_tautness()

        grid = self.grid.copy_grid()
        pairings = self.grid.worst_pairings()
        try:
            while (not exhausted):
                worst = self.grid.worst_cells()
                pair = 0
                move_on = False
                while (not move_on) & (pair < len(pairings)) & (not exhausted):
                    n += 1
                    self.update_trial(n)
                    
                    cells = worst[pairings[pair][0]],worst[pairings[pair][1]]
                    cell1 = tuple(cells[0])
                    cell2 = tuple(cells[1])

                    swap = grid.check_swap(cell1,cell2)

                    if swap:
                        swap+=1
                        input('SWAP{}'.format(swaps))
                        grid.swap_pictures(cell1,cell2)
                        taut_1 = grid.get_tautness()
                        self.update_trial(n,taut_1)
                        move_on = True
                    else:
                        pair += 1
                        if pair == len(pairings):
                            exhausted = True

                    if n == trials:
                        exhausted = True

        except KeyboardInterrupt:
            pass

        print()
        self.grid = grid
        return grid

    def save_grid(self):
        return

    def update_trial(self,n,taut=None):
        # update on trial and result
        improve_text = ' | strength: '
        if taut is not None:
            spaces = ' '  if taut < 1 else ''
            improvement = '{}{:0.2%}{}'.format(improve_text,taut,spaces)
        else:
            spaces = ' '*(len(improve_text)+len('100.0%'))
            improvement = ''
        print(' Trial {}{}'.format(n,improvement,spaces),end='\r')



#            if time_to_print:
#                next_name = find_next_name(folder,name,extension,number=True)
#                grid.save_output(folder=folder,name=next_name,extension=extension,secondary_scale=secondary_scale,
#                                 display=display,print_strength=True)

#                time_to_print = False
 

class Printer:
    def print_grid(grid:Grid,library=None,border=0,border_color=None):
        return

    def print_gif(temp_path,folder,save_name,extension='jpg',gif_extension='gif',dimension=200,durations=[500,1000]):
        files = sorted([fn for fn in os.listdir(temp_path) if '.{}'.format(extension) in fn])
        # save intermediate steps as a gif and move out of temp folder

        if len(files) > 1:
            height,width = Image.open('{}/{}'.format(temp_path,files[0])).size
            dimension_height = round(dimension)
            dimension_width = round(dimension/height*width)

            imgs = [Image.open('{}/{}'.format(temp_path,fn)).resize((dimension_height,dimension_width)) for fn in files]
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

def finalize_grid(grid,library,folder,save_name,extension='jpg',
                  dimension=200,border=0,border_color=(255,255,255)):
    # print final grid with border
    if type(border_color) is str:
        border_color = Rainbow.get_rgb(border_color,scaled=False)
        if border_color is None:
            border_color = (0,0,0)

    grid.save_output(folder=folder,name=save_name,extension=extension,library=library,dimension=dimension,
                     display='save',border=border,border_color=border_color)

#def save_gifs(temp_path,folder,save_name,extension='jpg',gif_extension='gif',dimension=200,durations=[500,1000]):
#    files = sorted([fn for fn in os.listdir(temp_path) if '.{}'.format(extension) in fn])
#    # save intermediate steps as a gif and move out of temp folder

#    if len(files) > 1:
#        height,width = Image.open('{}/{}'.format(temp_path,files[0])).size
#        dimension_height = round(dimension)
#        dimension_width = round(dimension/height*width)

#        imgs = [Image.open('{}/{}'.format(temp_path,fn)).resize((dimension_height,dimension_width)) for fn in files]
#        duration = durations[0]
#        repeats = durations[1]//durations[0]
#        append_images = imgs[1:-1] + [imgs[-1]]*repeats

#        imgs[0].save('{}/{}.{}'.format(folder,save_name,gif_extension),save_all=True,duration=duration,append_images=append_images,loop=0)

#        # delete all but final file
#        for fn in files[:-1]:
#            os.remove('{}/{}'.format(temp_path,fn))

#    # move final file and remove temp folder
#    last_file = '{}/{}'.format(temp_path,files[-1])
#    move_file = '{}/{}.{}'.format(folder,save_name,extension)
    
#    os.rename(last_file,move_file)

#    if len(os.listdir(temp_path)) == 0:
#        os.removedirs(temp_path)