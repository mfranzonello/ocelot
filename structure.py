### STRUCTURE OBJECTS ###
from common import *
from coloring import *
from media import *
from access import *
from layout import *
import time
import sys
import os

class Project:
    def __init__(self,project_path,photos_path,profile_path=False,stories_path=False,videos_path=False,
                 ig_username=None,download_path='downloads'):
        self.project_path = project_path
        self.photos_path = photos_path
        self.profile_path = profile_path
        self.stories_path = stories_path
        self.videos_path = videos_path
        self.username = ig_username
        self.download_path = download_path

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
        self.photos_path = project.photos_path
        self.profile_path = project.profile_path
        self.stories_path = project.stories_path
        self.videos_path = project.videos_path
        self.tick = tick
        self.username = project.username
        self.download_path = project.download_path

        self.library = Library()

        if self.username:
            self._check_ig()

        print('Looking for files...')
        self._get_pictures()
        if self.profile_path:
            self._get_profile()
        if self.stories_path:
            self._get_stories()
        if self.videos_path:
            self._get_videos()

    def _check_ig(self):
        # look if new media is in instagram
        ig_user = IGAccount('mf_traveler')
        ig_downloader = IGDownloader(ig_user,photos_path=self.photos_path,videos_path=self.videos_path,
                                     profile_path=self.profile_path,download_path=self.download_path)
        ig_downloader.download_media()
        ### STORIES??

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
        self._get_photos(self.photos_path)
        
    def _get_profile(self):
        # find profile pic
        print(' + profile',end='')
        sys.stdout.flush()
        self._get_photos(self.profile_path)
        
    def _get_stories(self):
        # find stories
        print(' + stories',end='')
        sys.stdout.flush()
        self._get_photos(self.stories_path)
        
    def _get_videos(self,in_extensions=['mp4']):
        # find videos and turn to photos
        print(' + videos',end='')
        sys.stdout.flush()
        files = find_files(self.videos_path,extensions=in_extensions)
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
                    grey_threshold=16,dark_threshold=100,round_threshold=16,dimension=50,aspect=None,
                    randomize=True,stories='stories',videos='videos',center=None):
        
        if remove_duplicates:
            library = self._remove_duplicates()
        else:
            library = self.library

        gallery = Gallery.from_library(library,round_color=round_color,grey_pct=grey_pct,dark_pct=dark_pct,
                                       grey_threshold=grey_threshold,dark_threshold=dark_threshold,round_threshold=round_threshold,
                                       dimension=dimension,aspect=aspect,randomize=randomize,stories=stories,videos=videos,
                                       center=center)

        self.gallery = gallery

    def get_gallery(self):
        gallery = self.gallery
        return gallery

class Printer:
    def __init__(self,collector:Collector,name='',dimension=200,dimension_small=20,
                 border_scale=0,border_color=(0,0,0),target_aspect=None,debugging=False):
        self.project_path = collector.project_path
        self.library = collector.library
        self.libary = collector.library

        self.name = name
        self.dimension = dimension
        self.dimension_small = dimension_small
        self.border_scale = border_scale
        self.border_color = border_color
        
        self.debugging = debugging

        self.height = 0
        self.width = 0
        self.images = []
        if target_aspect:
            self.target_aspect = target_aspect[0]/target_aspect[1]
        else:
            self.target_aspect = None

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
        self.height = grid.height
        self.width = grid.width

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

    def finalize(self,extension='jpg',gif=False,durations=[500,1000]):
        # save intermediate steps as a gif
        extensions = [extension]
        if gif:
            gif_extension = 'gif'
            extensions.append(gif_extension)
        save_name = self._find_next_name(self.project_path,self.name,extensions,number=True)
        
        # save final grid as full-size render
        final_image = self.images[-1]
        if self.target_aspect:
            current_aspect = final_image.height / final_image.width
            # narrower than ratio means stretch width
            if current_aspect > self.target_aspect:
                x = 0
                y = int(final_image.height/self.target_aspect - final_image.width)

            # wider than ratio means stretch height
            else:
                x = int(final_image.width*self.target_aspect - final_image.height)
                y = 0

            paste_box = (int(y/2),int(x/2),int(y/2)+final_image.width,int(x/2)+final_image.height)
            image_save = Image.new('RGB',(final_image.width+y,final_image.height+x))
            
            image_save.paste(final_image,paste_box)
        else:
            image_save = final_image

        image_save.save('{}/{}.{}'.format(self.project_path,save_name,extension))

        # save all steps as small size animation
        if gif:
            image_sizing = self.images[0]
            gif_height = int(self.dimension_small * self.height)
            gif_width = int(self.dimension_small * self.width)

            imgs = [im.resize((gif_width,gif_height)) for im in self.images]
            duration = durations[0]
            repeats = durations[1]//durations[0]
            append_images = imgs[1:-1] + [imgs[-1]]*repeats

            imgs[0].save('{}/{}.{}'.format(self.project_path,save_name,gif_extension),
                            save_all=True,duration=duration,append_images=append_images,loop=0)

        os.startfile(self.project_path)