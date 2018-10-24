### STRUCTURE OBJECTS ###
from common import *
from coloring import *
from media import *
from access import *
from layout import *
from plotting import *
import time
import sys
import os

class Project:
    # read in inputs.txt and create variables
    def __init__(self,inputs_file='inputs.txt',
                 debugging=False,angle_weight=2,distance_weight=3,dark_weight=1,difference_weight=6,print_after=1000,secondary_scale=1/3):

        tweak_split = '='
        parameters = {}
        f = open(inputs_file,'r')
        for line in f:
            if (line[0] != '#') & (tweak_split in line):
                keyvalue = [text.strip() for text in line.split(tweak_split)]
                if len(keyvalue) == 2:
                    key,value = keyvalue
                    parameters[key] = self._get_value(value)
        f.close()

        # inputs
        # where is the project located
        self.path = parameters.get('path')
        self.ig_username = parameters.get('ig_username')

        # how is the project structured?
        self.photos_folder = parameters.get('photos_folder')
        self.profile_folder = parameters.get('profile_folder')
        self.stories_folder = parameters.get('stories_folder')
        self.videos_folder = parameters.get('videos_folder')
        self.downloads_folder = parameters.get('downloads_folder')
        self.out_folder = parameters.get('out_folder')

        # how should the output look?
        self.grid_name = parameters.get('grid_name')
        self.grid_extension = parameters.get('grid_extension')
        self.grid_dimension = parameters.get('grid_dimension')
        self.grid_shape = parameters.get('grid_shape')

        aspects = {'iphonex':(19.5,9),
                   'iphone':(16,9),
                   'square':(1,1),
                   'golden':(1,1.618),
                   'story':(1921,1080)}
        self.grid_aspect = aspects.get(parameters.get('grid_aspect'),parameters.get('grid_aspect'))
        self.grid_aspect_force = parameters.get('grid_aspect_force')
        
        self.grid_border_scale = parameters.get('grid_border_scale')
        self.grid_border_color = parameters.get('grid_border_color')
        self.grid_gif = parameters.get('grid_gif')

        # what content should be used?
        self.check_ig = parameters.get('check_ig')
        self.use_profile = parameters.get('use_profile')
        self.use_stories = parameters.get('use_stories')
        self.use_videos = parameters.get('use_videos')
        self.video_tick = parameters.get('video_tick')
        self.remove_duplicates = parameters.get('remove_duplicates')
        self.profile_size = parameters.get('profile_size')

        # how refined should the process be?
        self.trials = parameters.get('trials')

        weights = sum([angle_weight,distance_weight,dark_weight,difference_weight])
        self.angle_weight = angle_weight/weights
        self.distance_weight = distance_weight/weights
        self.dark_weight = dark_weight/weights
        
        # should the intermediate steps be saved?
        self.print_after = print_after
        self.secondary_scale = secondary_scale

        # special mode
        self.debugging = debugging
        self.parameters = parameters
        self.runs = range(parameters.get('runs',1))

        # project specific
        self.project_path = '{}/{}'.format(self.path,self.out_folder)
        self.photos_path = '{}/{}'.format(self.path,self.photos_folder)
        self.profile_path = '{}/{}'.format(self.path,self.profile_folder) if self.use_profile else False
        self.stories_path = '{}/{}'.format(self.path,self.stories_folder) if self.use_stories else False
        self.videos_path = '{}/{}'.format(self.path,self.videos_folder) if self.use_videos else False
        self.username = self.ig_username if self.check_ig else None
        self.download_path = self.downloads_folder

        self.start_time = self._timer()
        self.iterations = 0
        self.results = []

        lattice = {'rectangular':'cartesian'}.get(self.grid_shape,self.grid_shape)
        self.coordinate_system = CoordinateSystem(lattice)
        ##self.coordinate_matrix = None

    def _get_value(self,string):
        # remove end comments, apostrophes and extra spaces
        if '#' in string:
            string = string[:string.index('#')]
        if string[0] == '\'' and string.rfind('\'') > 0:
            string = string[1:string.rfind('\'')]
        string = string.strip()

        # tuples
        if type(string) is tuple:
            value = string
        elif all(char in string for char in ['(',',',')']):
            value = self._get_tuple(string)

        # numbers
        elif string.isdigit():
            value = int(string)
        elif all((s.isnumeric() for s in string if s != '.')):
            value = float(string)
        elif '/' in string:
            value = self._get_fraction(string)

        # booleans, None and strings
        else:
            value = {'True':True,'False':False,'None':None}.get(string,string)

        return value

    def _get_tuple(self,string):
        # tuples (X,Y,...)
        value = tuple(self._get_value(v) for v in string[1:-1].split(','))
        return value

    def _get_fraction(self,string):
        # fractional values X/Y
        numden = string.split('/')
        if (len(numden) == 2) and (numden[0].isnumeric() & numden[1].isnumeric()):
            numerator,denominator = numden
            value = float(numerator)/float(denominator)
        else:
            value = string

        return value

    def _timer(self,last_time=None):
        # mark time and return time from previous timer
        current_time = time.time()
        if last_time is None:
            time_elapsed = None
        else:
            time_elapsed = current_time - last_time[0]
        return current_time,time_elapsed

    def add_result(self,period:str,result:float):
        # update project
        if period == 'iterations':
            self.iterations = result
        else:
            self.results.append([period.capitalize(),result])
        return

    def summarize(self):
        # print project results
        end_time = self._timer(self.start_time)
        print('Ran {} iterations'.format(self.iterations))
        for result in self.results:
            print('{} strength: {:0.2%}'.format(result[0],result[1]))
        print('Elapsed time: {} min {} sec'.format(int(end_time[1]/60),round(end_time[1]%60)))

class Finder:
    # finds media to use and coverts to images
    def __init__(self,project:Project):
        self.project = project
        self.library = Library()

    def find(self):
        # look for files and links and convert
        if self.project.username:
            self._check_ig()

        print('Looking for files...')
        self._get_pictures()
        if self.project.profile_path:
            self._get_profile()
        if self.project.stories_path:
            self._get_stories()
        if self.project.videos_path:
            self._get_videos()

    def _check_ig(self):
        # look if new media is in instagram
        ig_user = IGAccount(self.project.username)
        ig_user.ping()
        ig_downloader = IGDownloader(ig_user,photos_path=self.project.photos_path,videos_path=self.project.videos_path,
                                     profile_path=self.project.profile_path,download_path=self.project.download_path)
        ig_downloader.download_media()
        ### STORIES??

    def _get_photos(self,folder,in_extensions=['jpg','png','bmp','gif'],crop=False):
        # find posted photos, profile or stories
        files = Common.find_files(folder,extensions=in_extensions)
        photos = [Photo(fn) for fn in files]
        if crop:
            photos = [j for k in [p.crop_photo() for p in photos] for j in k]
        library = Library(photos)
        self.library.merge_library(library)

    def _get_movies(self,folder,in_extensions=['mp4'],first_only=False):
        # find posted stories or videos
        files = Common.find_files(folder,extensions=in_extensions)
        library = Library()
        for fn in files:
            video = Video(fn)
            library.add_photos(video.get_photos(tick=self.project.video_tick,first_only=first_only))
        self.library.merge_library(library)
        
    def _get_pictures(self):
        # find posted photos
        print(' ...checking photos',end='')
        sys.stdout.flush()
        self._get_photos(self.project.photos_path)
        
    def _get_profile(self):
        # find profile pic
        print(' + profile',end='')
        sys.stdout.flush()
        self._get_photos(self.project.profile_path)
        
    def _get_stories(self):
        # find stories
        print(' + stories',end='')
        sys.stdout.flush()
        self._get_photos(self.project.stories_path,crop=True)
        self._get_movies(self.project.stories_path,first_only=True)

    def _get_videos(self):
        # find videos and turn to photos
        print(' + videos',end='')
        sys.stdout.flush()
        self._get_movies(self.project.videos_path)
        
    def get_library(self):
        # return merged libraries
        print('\n ...found {} images'.format(self.library.size()))
        return self.library

class Collector:
    def __init__(self,finder:Finder):
        self.library = finder.get_library()
        self.gallery = None
        self.project = finder.project
        ##self.coordinate_system = None
        print('\nAnalyzing images...')

    def _remove_duplicates(self):
        library = self.library
        purge_count = library.purge()
        if purge_count > 0:
            print(' ...removed {} duplicate photo{}'.format(purge_count,'s' if purge_count > 1 else ''))
        return library

    def create_gallery(self,remove_duplicates=True,round_color=True,grey_pct=0.75,dark_pct=0.6,
                    grey_threshold=16,dark_threshold=100,round_threshold=16,dimension=50,aspect=None,
                    randomize=True,stories='stories',videos='videos',center=None):##,lattice=None):
        
        ##self.coordinate_system = CoordinateSystem(lattice)
        if remove_duplicates:
            library = self._remove_duplicates()
        else:
            library = self.library

        gallery = Gallery.from_library(library,round_color=round_color,grey_pct=grey_pct,dark_pct=dark_pct,
                                       grey_threshold=grey_threshold,dark_threshold=dark_threshold,round_threshold=round_threshold,
                                       dimension=dimension,aspect=aspect,randomize=randomize,stories=stories,videos=videos,
                                       center=center)##,coordinate_system=self.coordinate_system)

        self.gallery = gallery

    def get_gallery(self):
        gallery = self.gallery
        return gallery

class Printer:
    def __init__(self,collector:Collector,name='',dimension=200,dimension_small=20,
                 border_scale=0,border_color=(0,0,0),target_aspect=None,debugging=False):
        self.project = collector.project
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
        self.width2 = 0

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

        # print imags at full resolution
        if full:
            library = self.library
            dimension = self.dimension
            border = round(self.border_scale * self.dimension)
            border_color = self.border_color
            secondary_scale = False
            print_strength = False

        # print colors only
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

    def finalize(self,durations=[500,1000]):
        # save intermediate steps as a gif
        extension = self.project.grid_extension
        extensions = [extension]

        gif = self.project.grid_gif
        if gif:
            gif_extension = 'gif'
            extensions.append(gif_extension)
        save_name = self._find_next_name(self.project.project_path,self.name,extensions,number=True)
        
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

        image_save.save('{}/{}.{}'.format(self.project.project_path,save_name,extension))

        # save all steps as small size animation
        if gif:
            image_sizing = self.images[0]
            gif_height = int(self.dimension_small * self.height)
            gif_width = int(self.dimension_small * self.width)

            imgs = [im.resize((gif_width,gif_height)) for im in self.images]
            duration = durations[0]
            repeats = durations[1]//durations[0]
            append_images = imgs[1:-1] + [imgs[-1]]*repeats

            imgs[0].save('{}/{}.{}'.format(self.project.project_path,save_name,gif_extension),
                            save_all=True,duration=duration,append_images=append_images,loop=0)

        os.startfile(self.project.project_path)