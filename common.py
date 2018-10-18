### METHODS USED ACROSS MODULES ###
import os
import math
import time
import numpy

def sort_by_list(input,rank_list,reverse=False):
    # return list sorted by another list
    sort_flip = -1 if reverse else 1
    arr1 = numpy.array(input)
    arr2 = numpy.array(rank_list)
    sorted_list = arr1[arr2.argsort()[::sort_flip]].tolist()
    return sorted_list

def find_next_name(folder,name,extensions,number=False):
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

def find_next_subfolder(folder,name,number=False):
    # find the next available subfolder for a given name pattern
    subfolders = next(os.walk(folder))[1]
    name_try = name
    n = 0
    # add subnumber if mandatory
    if number:
        name_try = '{}_{:02}'.format(name,n)
    while '{}'.format(name_try) in subfolders:
        n += 1
        name_try = '{}_{:02}'.format(name,n)
    os.makedirs('{}/{}'.format(folder,name_try))
    return name_try

def find_files(folder,extensions=['']):
    # find files in a subfolder with an extension
    files = []
    folders = [fold[0] for fold in os.walk(folder)]
    files += [fl+'/'+fn for fl in folders for fn in os.listdir(fl) if (any('.'+ext in fn for ext in extensions))]
    return files

def open_folder(folder):
    # open folder to show results
    os.startfile(folder)

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

def timer(last_time=None):
    # mark time and return time from previous timer
    current_time = time.time()
    if last_time is None:
        time_elapsed = None
    else:
        time_elapsed = current_time - last_time[0]
    return current_time,time_elapsed

def rms(array):
    rms = math.sqrt(sum([i**2 for i in array])/len(array))
    return rms