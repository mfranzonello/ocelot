### STRUCTURE OBJECTS ###
from common import *
from coloring import *
from media import *
from layout import *
import time
import sys
import os

class Project:
    def __init__(self,project_path,photos_path,profile_path=False,stories_path=False,videos_path=False):
        self.project_path = project_path
        self.photos_path = photos_path
        self.profile_path = profile_path
        self.stories_path = stories_path
        self.videos_path = videos_path

        self.start_time = self._timer()
        self.iterations = 0
        self.results = []

    def _timer(self,last_time=None):
        # mark time and return time from previous timer
        current_time = time.time()
        if last_time is None:
            time_elapsed = None
        else:
            time_elapsed = current_time - last_time[0]
        return current_time,time_elapsed

    def add_result(self,period:str,result:float):
        if period == 'iterations':
            self.iterations = result
        else:
            self.results.append([period.capitalize(),result])
        return

    def summarize(self):
        end_time = self._timer(self.start_time)
        print('Ran {} iterations'.format(self.iterations))
        for result in self.results:
            print('{} strength: {:0.2%}'.format(result[0],result[1]))
        print('Elapsed time: {} min {} sec'.format(int(end_time[1]/60),round(end_time[1]%60)))

class Finder:
    def __init__(self,project:Project,tick=30):
        self.project_path = project.project_path
        self.pictures_folder = project.photos_path
        self.profile_folder = project.profile_path
        self.stories_folder = project.stories_path
        self.videos_folder = project.videos_path
        self.tick = tick
        self.library = Library()

        print('Looking for files...')
        self._get_pictures()
        if self.profile_folder:
            self._get_profile()
        if self.stories_folder:
            self._get_stories()
        if self.videos_folder:
            self._get_videos()

    def _find_files(self,folder,extensions=['']):
        # find files in a subfolder with an extension
        files = []
        folders = [fold[0] for fold in os.walk(folder)]
        files += [fl+'/'+fn for fl in folders for fn in os.listdir(fl) if (any('.'+ext in fn for ext in extensions))]
        return files

    def _get_photos(self,folder,in_extensions=['jpg','png','bmp','gif']):
        # find posted photos, profile or stories
        files = self._find_files(folder,extensions=in_extensions)
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
        
    def _get_videos(self,in_extensions=['mp4']):
        # find videos and turn to photos
        print(' + videos',end='')
        sys.stdout.flush()
        files = self._find_files(self.videos_folder,extensions=in_extensions)
        library = Library()
        for fn in files:
            video = Video(fn)
            library.add_photos(video.get_photos(tick=self.tick))
        self.library.merge_library(library)

    def get_library(self):
        print('\n ...found {} images'.format(self.library.size()))
        return self.library

class Collector:
    def __init__(self,finder:Finder):
        self.library = finder.get_library()
        self.gallery = None
        self.project_path = finder.project_path
        print('\nAnalyzing images...')

    def _remove_duplicates(self):
        library = self.library
        purge_count = library.purge()
        if purge_count > 0:
            print(' ...removed {} duplicate photo{}'.format(purge_count,'s' if purge_count > 1 else ''))
        return library

    
    def create_gallery(self,remove_duplicates=True,round_color=True,grey_pct=0.75,dark_pct=0.6,
                    grey_threshold=16,dark_threshold=100,round_threshold=16,dimension=50,square=True,
                    randomize=True,stories='stories',videos='videos'):
        
        if remove_duplicates:
            library = self._remove_duplicates()
        else:
            library = self.library

        gallery = Gallery.from_library(library,round_color=round_color,grey_pct=grey_pct,dark_pct=dark_pct,
                                       grey_threshold=grey_threshold,dark_threshold=dark_threshold,round_threshold=round_threshold,
                                       dimension=dimension,square=square,randomize=randomize,stories=stories,videos=videos)

        self.gallery = gallery

    def get_gallery(self):
        gallery = self.gallery
        return gallery

class Printer:
    def __init__(self,collector:Collector,name='',dimension=200,dimension_small=50,
                 border_scale=0,border_color=(0,0,0),debugging=False):
        self.project_path = collector.project_path
        self.library = collector.library
        self.libary = collector.library

        self.name = name
        self.dimension = dimension
        self.dimension_small = dimension_small
        self.border_scale = border_scale
        self.border_color = border_color
        
        self.debugging = debugging

        self.images = []

    def _find_next_name(self,folder,name,extensions,number=False):
        # find the next available file for a given name pattern
        if type(extensions) is str:
            extensions = [extensions]
        files = os.listdir(folder)
        name_try = name
        n = 0
        # add subnumber if mandatory
        if number:
            name_try = '{}_{:02}'.format(name,n)
        while any('{}.{}'.format(name_try,ex) in files for ex in extensions):
            n += 1
            name_try = '{}_{:02}'.format(name,n)
        return name_try
      
    def store_grid(self,grid:Grid,full=False,vibrant=True,display=False):
        # store a grid result image
        if full:
            library = self.library
            dimension = self.dimension
            border = round(self.border_scale * self.dimension)
            border_color = self.border_color
            secondary_scale = False
            print_strength = False
        else:
            library = None
            dimension = self.dimension_small
            border = 0
            border_color = None
            secondary_scale = self.debugging
            print_strength = self.debugging

        grid_image = grid.save_output(dimension=dimension,library=library,
                         secondary_scale=secondary_scale,vibrant=True,border=border,border_color=border_color,
                         print_strength=print_strength)
        self.images.append(grid_image)
        return

    def finalize(self,extension='jpg',gif_extension='gif',durations=[500,1000]):
        # save intermediate steps as a gif
        save_name = self._find_next_name(self.project_path,self.name,[extension],number=True)
        
        # save final grid as full-size render
        self.images[-1].save('{}/{}.{}'.format(self.project_path,save_name,extension))

        # save all steps as small size animation
        gif_height,gif_width = self.images[1].size
        #dimension_height = round(self.dimension_small)
        #dimension_width = round(self.dimension_small/height*width)
        imgs = [im.resize((gif_height,gif_width)) for im in self.images]
        duration = durations[0]
        repeats = durations[1]//durations[0]
        append_images = imgs[1:-1] + [imgs[-1]]*repeats

        imgs[0].save('{}/{}.{}'.format(self.project_path,save_name,gif_extension),
                        save_all=True,duration=duration,append_images=append_images,loop=0)

        os.startfile(self.project_path)