### MEDIA OBJECTS ###
from common import *
from coloring import *

from PIL import Image,ImageChops
import cv2

class Photo:
    # image with an id
    def __init__(self,fn,image=None):
        self.id = fn
        if image is None:
            if any('.{}'.format(ext) in fn for ext in ['jpg','jpeg','gif','tif','bmp','png']):
                image = Image.open(fn)
            elif any('.{}'.format(ext) in fn for ext in ['avi','mp4','mov']):
                video = Video(fn)
                image = video.get_photos(first_only=True)
            else:
                image = None
        self.image = image

    def crop_photo(self,cut_range=20,std_threshold=5,color_threshold=(1,1,1)):
        # see if there is a line in the middle of the photo and split image
        mean_threshold = Color(0,0,0).difference(Color(*color_threshold))
        scores = []
        means = []
        boundary = False
        image = self.image
        w,h = image.size
        # check each line from slightly above to slightly below middle
        for i in range(-cut_range,cut_range):
            arr = numpy.array([image.getpixel((x,int(h/2)+i)) for x in range(w)])
            scores.append(arr.std(0).max())
            means.append(Color(*tuple(arr.mean(0))))

        # check if a boundary pattern exists
        if (min(scores) < std_threshold) & (max(scores) >= std_threshold):
            for s in range(1,len(scores)-1):
                if (scores[s] < std_threshold):
                    if max(means[s].difference(means[s-1]),
                           means[s].difference(means[s+1])) > mean_threshold:
                        boundary = True

        # if a boundary exists then crop image
        if boundary:
            crop_box_top = (0,0,w,int(h/2))
            crop_box_bottom = (0,int(h/2),w,h)
            photos = [Photo(self.id,image.crop(crop_box)) for crop_box in [crop_box_top,crop_box_bottom]]
        else:
            photos = [self]

        return photos

class Video:
    # video that can be split into images
    def __init__(self,fn):
        self.id = fn
        return

    def _cv2_to_image(self,cv2_image):
        # convert OpenCV image format to Pillow image format
        im = Image.fromarray(cv2.cvtColor(cv2_image,cv2.COLOR_BGR2RGB))
        return im

    def get_photos(self,tick=60,first_only=False):
        # export periodic frames as images
        cap = cv2.VideoCapture(self.id)

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames = [0] if first_only else range(0,frame_count,tick)

        photos = []
        for f in frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES,f)
            success,cv2_image = cap.read()
            photos.append(Photo('{}_{}'.format(self.id,len(photos)),self._cv2_to_image(cv2_image)))

        cap.release()

        return photos

class Library:
    # collection of photos
    def __init__(self,photos=None):
        self.photos = {}
        if photos is not None:
            self.add_photos(photos)

    def add_photo(self,photo:Photo):
        # add a photo to library
        if photo.id not in self.photos:
            self.photos[photo.id] = photo

    def add_photos(self,photos_list):
        # add photos to library
        for photo in photos_list:
            self.add_photo(photo)

    def get_photo(self,fn):
        # return a photo with id
        return self.photos.get(fn)

    def merge_library(self,library):
        # combine two libraries
        self.photos.update(library.photos)

    def purge(self,dimension=10,threshold=0.9,greys=50):
        # remove duplicate photos based on pixel content
        dimensions = (dimension,dimension)
        size = dimension**2
        photos = self.photos.copy()
        uniques = []
        for photo in self.photos:
            image = self.photos[photo].image.resize(dimensions)
            diff = 0
            n = 0
            if len(uniques) > 0:
                while (diff < threshold) & (n < len(uniques)):
                    diff = max(diff,sum(ImageChops.difference(image,uniques[n]).histogram()[0:greys])/size)
                    n += 1

            if diff >= threshold:
                photos.pop(photo)
            else:
                uniques.append(image)

            analyzed = list(self.photos.keys()).index(photo)/len(self.photos)
            print(' ...verified {:0.1%}'.format(analyzed),end='\r')

        print(' ...verified 100% ')

        purge_count = len(self.photos) - len(uniques) #len(photos)
        self.photos = photos

        return purge_count

    def size(self):
        # return number of photos in library
        return len(self.photos)

class Pixelation:
    # a compressed image with a filename and prominent color
    # can ignore dark or grey pixels to find vibrancy
    def __init__(self,photo:Photo,round_color=False,grey_pct=100,dark_pct=100,
                 grey_threshold=16,dark_threshold=100,round_threshold=16,
                 dimension=0):
        self.im = photo.image.resize((min(10,dimension),min(10,dimension)))
        self.id = photo.id
        self.display = '~/'+self.id[self.id.rfind('/')+1:]

        h,w = self.im.size
        if h != w:
            m = min(h,w)//2
            self.im = self.im.crop((int(h/2-m/2),int(w/2-m/2),int(h/2+m/2),int(w/2+m/2)))

        self.height = self.im.height
        self.width = self.im.width
        self.size = self.height * self.width
        self.freq,self.pixels = list(zip(*self.im.getcolors(self.size)))
        
        self.colors = {}
        self.colors_dull = {}

        self.prominence = []
        self.prominence_dull = []

        self.sorted = False

        if round_color:
            self.nearest_color(grey_pct,dark_pct)

    def nearest_color(self,grey_pct=100,dark_pct=100,
                      grey_threshold=16,dark_threshold=100,round_threshold=16):
        # compress image and determine what its most prominent vibrant color
        print(' ...extracting colors for {}'.format(self.display),end='\r')

        darks = {}
        greys = {}
        vibrants = {}

        for c in range(len(self.pixels)):
            red,green,blue = self.pixels[c]
            color = Color(red,green,blue)
            red,green,blue = color.nearest_color(threshold=round_threshold)

            if color.is_dark(threshold=dark_threshold):
                darks[(red,green,blue)] = darks.get((red,green,blue),0) + self.freq[c]
            elif color.is_grey(threshold=grey_threshold):
                greys[(red,green,blue)] = greys.get((red,green,blue),0) + self.freq[c]
            else:
                vibrants[(red,green,blue)] = vibrants.get((red,green,blue),0) + self.freq[c]
               
        if (len(vibrants) == 0) | (sum(darks.values()) > dark_pct*self.size):
            vibrants.update(darks)
        if (len(vibrants) == 0) | (sum(darks.values()) > grey_pct*self.size):
            vibrants.update(greys)

        self.colors = vibrants.copy()
        self.colors_dull = self.colors.copy()
        self.colors_dull.update(darks)
        self.colors_dull.update(greys)

        self.sort_colors()

    def sort_colors(self):
        # organize colors in image by order of appearance
        for color_set in [self.colors,self.colors_dull]:
            color_keys = list(color_set.keys())
            color_values = list(color_set.values())

            vals_sorted = sorted(color_values,reverse=True)
            colors_sorted = []

            for v in vals_sorted:
                v_index = color_values.index(v)
                colors_sorted += [color_keys[v_index]]
                color_keys.pop(v_index)
                color_values.pop(v_index)

            if color_set == self.colors:
                self.prominence = colors_sorted
            else:
                self.prominence_dull = colors_sorted

        self.sorted = True

    def prominent_color(self,n=0,vibrant=True):
        # return the most prominent vibrant color
        if not self.sorted:
            for color_set in [self.colors,self.all_colors]:
                self.sort_colors(color_set)
        if vibrant:
            prominence = self.prominence
        else:
            prominence = self.prominence_dull
            if len(prominence) == 0:
                prominence = self.prominence
        
        prominent_color = Color(*prominence[min(n,len(prominence))])
        return prominent_color

    def secondary_color(self,threshold=256):
        # return the most prominent color that is different from the most prominent color
        prominent = self.prominent_color()
        distance = 0
        n = 0
        best = None
        while (n < len(self.prominence)-1) & (distance < threshold):
            n += 1
            next_prominent = self.prominent_color(n)
            distance = prominent.difference(next_prominent)
            if (distance > threshold/2) & (best is not None):
                best = next_prominent
        if distance >= threshold:
            secondary = next_prominent
        elif best is not None:
            secondary = best
        else:
            best = self.prominent_color(vibrant=False)
            if prominent == best:
                n = 1
                distance = 0
                color_count = max(len(self.prominence_dull),len(self.prominence))
                while (n < color_count) & (distance < threshold/2):
                    best = self.prominent_color(n=n,vibrant=False)
                    distance = prominent.distance(best)
                    n += 1
                if prominent == best:
                    best = self.prominent_color(n=-1,vibrant=False)
            secondary = best
        return secondary

class Picture:
    # color block with a linked file name and RGB weights
    def __init__(self,id,color,secondary=None,greyscale=None):
        self.id = id
        self.display = '~/'+id[id.rfind('/')+1:]
        self.color = color
        self.secondary = secondary
        self.greyscale = greyscale
        self.angle = self.color.angle
        self.target = None

    def __repr__(self):
        return 'ID: {} | {}'.format(self.display,self.color)

    def difference(self,picture):
        # return distance between prominent colors of two pictures
        if picture is None:
            distance = 0
        else:
            distance = self.color.difference(picture.color)
        return distance

    def hue_angle(self,color:Color):
        color.get_rv

class Gallery:
    # collection of colors with order
    def __init__(self,pictures,randomize=True,stories='stories',videos='videos',center=None):
        self.center = None
        if center:
            if center in pictures:
                self.center = center
            else:
                center_pics = [p for p in pictures if self._folder_in_id(center,p.id)]
                if len(center_pics):
                    self.center = center_pics[0]
            pictures = [p for p in pictures if p != self.center]

        if randomize:
            pictures1 = [p for p in pictures if not any((self._folder_in_id(stories,p.id),self._folder_in_id(videos,p.id)))]
            pictures2 = [p for p in pictures if all((self._folder_in_id(stories,p.id),not self._folder_in_id(videos,p.id)))]
            pictures3 = [p for p in pictures if self._folder_in_id(videos,p.id)]
            random.shuffle(pictures1)
            random.shuffle(pictures2)
            random.shuffle(pictures3)
            pictures = pictures1 + pictures2 + pictures3

        self.pictures = pictures

        self.size = len(pictures)
        self.corners = {}
        self.angle = 0

    def __repr__(self):
        return ''.join(['{}\n'.format(picture) for picture in self.pictures])[:-len('\n')]

    def _folder_in_id(self,folder,id):
        slashes = ['\\','/']
        found = any(['{}{}{}'.format(slash1,folder,slash2) in id for slash1 in slashes for slash2 in slashes])
        return found

    def from_library(library,round_color=False,grey_pct=100,dark_pct=100,
                     grey_threshold=16,dark_threshold=100,round_threshold=16,
                     dimension=0,aspect=(1,1),randomize=True,stories='stories',videos='videos',center=None):
        # construct a gallery from a library
        pixelation = [Pixelation(library.get_photo(photo),round_color=round_color,
                                 grey_pct=grey_pct,dark_pct=dark_pct,
                                 grey_threshold=grey_threshold,dark_threshold=dark_threshold,
                                 round_threshold=round_threshold,
                                 dimension=dimension) for photo in library.photos]
        pictures = [Picture(px.id,px.prominent_color(),
                            secondary=px.secondary_color(),
                            greyscale=px.prominent_color(vibrant=False)) for px in pixelation]
        gallery = Gallery(pictures,randomize=randomize,stories=stories,videos=videos,center=center)
    
        print('\n')
    
        return gallery

    def get_picture(self,n):
        # return nth picture
        return self.pictures[n]

    def get_hsv_corner(self,color:Color,angle=0,hues=[]):
        # find corner for a color based on its HSV
        # angle determined by hue -- h is 0 to 1
        # for whiter pics (lower saturation), move to middle -- l is 0 to 1
        # for darker pics (lower vibrance), move away from middle -- v is 0 to 255
        h,s,v = color.hsv
        if len(hues) > 0:
            h = hues.index(h)/len(hues)
        H = angle_simplified(h * 2*math.pi + angle)
        S = s
        V = v/255
        R = 0.375

        # darkness outweighs whiteness
        dark = color.is_dark()
        if dark:
            S = 1

        x = max(0,min(1, R * math.cos(H) * S * (2-V)**2 + 0.5))
        y = max(0,min(1, R * math.sin(H) * S * (2-V)**2 + 0.5))
        
        return (x,y),dark,H

    def cycle_list(self,values,n):
        # return every nth element to distribute evenly
        cycled = [values[v] for m in range(n) for v in range(len(values)) if v%n == m]
        return cycled

    def order_pictures(self,stories='stories',videos='videos'):
        # assign an order to add pictures based on prominent color

        # place based on color wheel
        sorted_dark = []
        dark_hues = []
        sorted_vibrant = []
        vibrant_hues = []

        # place at an angle
        angle = angle_simplified(random.random()*2*math.pi)
        self.angle = angle_simplified(angle)

        hues = sorted([picture.color.hsv[0] for picture in self.pictures])

        for picture in self.pictures:
            # get corner and darkness
            self.corners[picture.id],dark,H = self.get_hsv_corner(picture.color,angle=angle,hues=hues)
            self.pictures[self.pictures.index(picture)].angle = H
            # order pictures based on darkness
            if dark:
                sorted_dark.append(picture)
                dark_hues.append(H)
            else:
                sorted_vibrant.append(picture)
                vibrant_hues.append(H)
    
        sorted_dark = sort_by_list(sorted_dark,dark_hues)
        sorted_vibrant = sort_by_list(sorted_vibrant,vibrant_hues)

        sorted_order = sorted_dark + self.cycle_list(sorted_vibrant,6)

        sorted_pics = [p for p in self.pictures if all(('/{}/'.format(stories) not in p.id,'/{}/'.format(videos) not in p.id))]
        sorted_stories = [p for p in self.pictures if all(('/{}/'.format(stories) in p.id,'/{}/'.format(videos) not in p.id))]
        sorted_videos = [p for p in self.pictures if '/{}/'.format(videos) in p.id]
        sorted_order = sorted_pics + sorted_stories + sorted_videos

        self.pictures = sorted_order    