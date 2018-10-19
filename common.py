### METHODS USED ACROSS MODULES ###
import math
import numpy

def sort_by_list(input,rank_list,reverse=False):
    # return list sorted by another list
    sort_flip = -1 if reverse else 1
    arr1 = numpy.array(input)
    arr2 = numpy.array(rank_list)
    sorted_list = arr1[arr2.argsort()[::sort_flip]].tolist()
    return sorted_list

def angle_simplified(angle):
    # returns angle in radians between -180 and 180 degrees
    in_circle = angle%(2*math.pi)
    angle_simple = in_circle if in_circle < math.pi else in_circle-2*math.pi
    return angle_simple

def angle_difference(angle1,angle2):
    # returns minimum difference between angles CW vs CCW
    angle1 = angle1 + 2*math.pi if angle1 < 0 else angle1
    angle2 = angle2 + 2*math.pi if angle2 < 0 else angle1
    diff = min(abs(angle1 - angle2),abs(angle2 - angle1))
    diff = min(diff,2*math.pi - diff)
    return diff