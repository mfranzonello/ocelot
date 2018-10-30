### MEDIA OBJECTS ###
from common import *
from coloring import *
from plotting import *
import random
from PIL import Image,ImageChops,ImageDraw
import cv2
import numpy

class Photo:
    # image with an id
    def __init__(self,fn,image=None):
        self.id = fn
        if image is None:
            if Common.extension_in(fn,['jpg','jpeg','gif','tif','bmp','png']):
                image = Image.open(fn)
            elif Common.extension_in(fn,['avi','mp4','mov']):
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

#        self._arange = numpy.arange(256) # length of colors in RGB bands

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
#    def purge(self,dimension=10,color_threshold=16,difference_threshold=0.9,greys=50):
        # remove duplicate photos based on pixel content
        ## FUTURE IDEA: split into RGB and sort by histograms
        ## only compare photos to other photos with similar range histograms
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
        #print('RESIZING1')
        #images = [print(p) if print(p) is not None else (p,self.photos[p].image.resize(dimensions)) for p in self.photos]
        #print('RESIZING2')
        ##uniques = []

        #averages = -numpy.ones([len(images),4],dtype=int) # empty array to store RGB
        
        #for i in range(len(images)):
        #    unique = True
        #    id = images[i][0]
        #    image = images[i][1]
        #    RGBs = [numpy.array(im.histogram()) for im in image.split()] # get RGB histograms
        #    photoRGB = [arr.dot(self._arange)/arr.sum() for arr in RGBs] # get average RGB
        #    similar_images = averages[(abs(averages[:,1] - photoRGB[0]) < color_threshold) & 
        #                              (abs(averages[:,2] - photoRGB[1]) < color_threshold) & 
        #                              (abs(averages[:,3] - photoRGB[2]) < color_threshold)] # compare RGB content for similar photos



        #    # look at differences only for similar photos
        #    while unique & (n < len(similar_images)):
        #        similar_image = images[similar_images[n,0]][1]

        #        negatives = max([sum(neg.histogram()[0:greys])/size for neg in ImageChops.difference(image,similar_image).split()])

        #        if negatives > difference_threshold/3:
        #            unique = False
        #        else:

        #    if unique:
        #        averages[i,:] = [1] + photoRGB # store averages 

        #    analyzed = i/len(images)
        #    print(' ...verified {:0.1%}'.format(analyzed),end='\r')

        #uniques = numpy.where(averages[:,0]==1)[0]
        #print(len(uniques))
        ##print(type(uniques))
        #input('BREAK')
        ##.tolist()
        #photos = {images[i][0]:self.photos[images[i][0]] for i in uniques}

        #    #diff = 0
        #    #n = 0
        #    #if len(uniques) > 0:
        #    #    while (diff < threshold) & (n < len(uniques)):
        #    #        diff = max(diff,sum(ImageChops.difference(image,uniques[n]).histogram()[0:greys])/size) ## WARNING! this might be looking at red pixels only
        #    #        n += 1

        #    #if diff >= threshold:
        #    #    photos.pop(photo)
        #    #else:
        #    #    uniques.append(image)

        #    #analyzed = list(self.photos.keys()).index(photo)/len(self.photos)
        #    #print(' ...verified {:0.1%}'.format(analyzed),end='\r')

        #print(' ...verified 100% ')

        #purge_count = len(self.photos) - len(photos) #len(uniques)
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
        self.dark = 0
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
    def __init__(self,pictures,randomize=True,stories='stories',videos='videos',center=None): ##,coordinate_system=CoordinateSystem()):
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
                     dimension=0,aspect=(1,1),randomize=True,stories='stories',videos='videos',center=None): ##,coordinate_system=CoordinateSystem()):
        # construct a gallery from a library
        pixelation = [Pixelation(library.get_photo(photo),round_color=round_color,
                                 grey_pct=grey_pct,dark_pct=dark_pct,
                                 grey_threshold=grey_threshold,dark_threshold=dark_threshold,
                                 round_threshold=round_threshold,
                                 dimension=dimension) for photo in library.photos]
        pictures = [Picture(px.id,px.prominent_color(),
                            secondary=px.secondary_color(),
                            greyscale=px.prominent_color(vibrant=False)) for px in pixelation]
        gallery = Gallery(pictures,randomize=randomize,stories=stories,videos=videos,center=center) ##,coordinate_system=coordinate_system)
    
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
        H = CoordinateSystem.angle_simplified(h * 2*math.pi + angle)
        S = s
        V = v/255
        R = 0.375

        # darkness outweighs whiteness
        dark = color.is_dark()
        if dark:
            S = 1
      
        return R,H,dark

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
        self.angle = CoordinateSystem.angle_simplified(random.random()*2*math.pi)
        
        hues = sorted([picture.color.hsv[0] for picture in self.pictures])

        for picture in self.pictures:
            # get corner and darkness
            R,H,dark = self.get_hsv_corner(picture.color,angle=self.angle,hues=hues)
            self.corners[picture.id] = (R,H)

            self.pictures[self.pictures.index(picture)].angle = H
            self.pictures[self.pictures.index(picture)].dark = dark

            # order pictures based on darkness
            if dark:
                sorted_dark.append(picture)
                dark_hues.append(H)
            else:
                sorted_vibrant.append(picture)
                vibrant_hues.append(H)
    
        sorted_dark = Common.sort_by_list(sorted_dark,dark_hues)
        sorted_vibrant = Common.sort_by_list(sorted_vibrant,vibrant_hues)

        sorted_order = sorted_dark + self.cycle_list(sorted_vibrant,6)

        sorted_pics = [p for p in self.pictures if all(('/{}/'.format(stories) not in p.id,'/{}/'.format(videos) not in p.id))]
        sorted_stories = [p for p in self.pictures if all(('/{}/'.format(stories) in p.id,'/{}/'.format(videos) not in p.id))]
        sorted_videos = [p for p in self.pictures if '/{}/'.format(videos) in p.id]
        sorted_order = sorted_pics + sorted_stories + sorted_videos

        self.pictures = sorted_order

class Shaper:
    # manipulations to an image
    def _cut(shape,size=1,dim=1):
        # return a pattern for a shape
        ratios = {'hexagon':math.sqrt(3)/2,
                  'circle':1}
        ratio = ratios[shape]

        if shape == 'circle':
            pattern = [0,0,1,1]
        elif shape == 'hexagon':
            resize = 2*size-1
            srange = range(3*size)

            pieces = [([(0.5,0),(0.5,0.5)][i>2*size][i%2],[(0.25,0.5),(0.25,-0.25)][i>2*size][i%2]) for i in srange]

            positions = [(-size,-0.5)]

            # set up pattern for NE
            for p in range(len(pieces)):
                position = positions[-1][0] + pieces[p][0], positions[-1][1] + pieces[p][1]
                positions.append(position)

            positions = [(positions[1][0],0)] + positions[2:] # delete starting adjustments

            positionsNE = [(p[0]/resize,p[1]/resize) for p in positions]

            # set up pattern for SE
            positionsSE = [(-positionsNE[-i-1][0],positionsNE[-i-1][1]) for i in srange]
            # set up pattern for SW
            positionsSW = [(-positionsNE[i][0],-positionsNE[i][1]) for i in srange]
            # set up pattern for NW
            positionsNW = [(positionsNE[-i-1][0],-positionsNE[-i-1][1]) for i in srange]

            # combine positions into pattern
            template = positionsNE[:-1] + positionsSE[:-1] + positionsSW[:-1] + positionsNW

        pattern = [(round((p[0]+0.5)*dim*ratio),
                    round((p[1]+0.5)*dim)) for p in template]
    
        return pattern,ratio

    def shape(image:Image,shape,size=1):
        # cut an image to a shape
        w,h = image.size
        dim = min(w,h)
        pattern,ratio = Shaper._cut(shape,size,dim)

        # convert to numpy and create mask
        imArray = numpy.asarray(image.convert('RGBA'))
        maskIm = Image.new('L',(imArray.shape[1],imArray.shape[0]),0)
        if shape == 'hexagon':
            ImageDraw.Draw(maskIm).polygon(pattern,outline=1,fill=1)
        elif shape == 'circle':
            ImageDraw.Draw(maskIm).ellipse(pattern,outline1=1,fill=1)
        mask = numpy.array(maskIm)

        # assemble new image (uint8: 0-255)
        newImArray = numpy.empty(imArray.shape,dtype='uint8')
        newImArray[:,:,:3] = imArray[:,:,:3] # colors (three first columns, RGB)
        newImArray[:,:,3] = mask*255 # transparency (4th column)

        shaped = Image.fromarray(newImArray,'RGBA')
        shaped.resize((int(w/ratio),int(h/ratio)),Image.ANTIALIAS)
        return shaped

    def blot(image:Image):
        # turn transparency to white:
        imArray = numpy.copy(numpy.asarray(image.convert('RGBA')))
        r,g,b,a = numpy.moveaxis(imArray,-1,0)
        r[a==0],g[a==0],b[a==0] = (255,255,255)
        newImArray = numpy.dstack([r,g,b,a])
        blotted = Image.fromarray(newImArray,'RGBA').convert('RGB')
        return blotted