### COLOR OBJECTS ###
from common import *
import math
import random
import colorsys

class Color:    
    # tuple of RGB
    def __init__(self,red,green,blue):
        self.red = red
        self.green = green
        self.blue = blue
        self.rgb = (self.red,self.green,self.blue)
        self.hsv = colorsys.rgb_to_hsv(self.red,self.green,self.blue)
        self.angle = angle_simplified(self.hsv[0] * 2*math.pi)

    def __repr__(self):
        string = 'R{:03}|G{:03}|B{:03}'.format(self.red,self.green,self.blue)
        return string
    
    def is_grey(self,threshold=16):
        # check if the RGB of a color are all close to each other
        greyness = math.sqrt((self.red - self.green)**2 +
                             (self.red - self.blue)**2 +
                             (self.green - self.blue)**2)
        grey = greyness < threshold*3
        return grey

    def is_dark(self,threshold=100):
        # check if the color is dim
        darkness = max(self.red,self.green,self.blue) < threshold
        return darkness

    def nearest_color(self,threshold=16):
        # put the color in a bucket
        red = int(round(self.red/threshold)*threshold)
        green = int(round(self.green/threshold)*threshold)
        blue = int(round(self.blue/threshold)*threshold)
        return red,green,blue

    def difference(self,color,method='rgb',r_weight=2,g_weight=4,b_weight=3,r_add_weight=128,coeff=0.005,scaled=True):
        # find the distance between two colors

        max_delta = 255

        # use euclidian RGB
        if method=='rgb':
            r_add = self.red + color.red
            r_delta = self.red - color.red
            g_delta = self.green - color.green
            b_delta = self.blue - color.blue
        
            distance = math.sqrt(r_weight*r_delta**2 + 
                                 g_weight*g_delta**2 + 
                                 b_weight*b_delta**2)# + 
                                 #r_add_weight*r_add*(r_delta**2-b_delta**2))

            if scaled:
                distance /= math.sqrt(r_weight*max_delta**2 + g_weight*max_delta**2 + b_weight*max_delta**2)

        # use HSV distance
        elif method=='hsv':
            h1,s1,v1 = self.hsv
            h2,s2,v2 = self.hsv
            distance = (math.sin(h1)*s1*v1 - math.sin(h2)*s2*v2)**2 \
                + (math.cos(h1)*s1*v1 - math.cos(h2)*s2*v2 )**2 \
                + coeff*(v1 - v2)**2

        return distance

    def primary_color(self,saturation_threshold=0.2,value_threshold=0.25):
        # find primary color using HSV
        h,s,v = self.hsv

        if v < value_threshold*255:
            primary = 'black'
        elif s < saturation_threshold:
            primary = 'white'
        else:
            primary = Rainbow.hues[round(h*len(Rainbow.hues))%len(Rainbow.hues)]

        primary_color = Rainbow.get_rgb(primary)

        return primary_color

class Pattern:
    # pattern order for RMBCGY+WK seeding
    def generate_pattern(hues=True,angle=False,account_for_angle=False):
        # return a pattern based on hue or a pre-determined mapping
        corners = {'hsv':True,'angle':angle,'hues':hues,'account for angle':account_for_angle}

        return corners