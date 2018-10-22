### METHODS USED ACROSS MODULES ###
import numpy
import os

class Common:
    # methods used throughout app
    def find_files(folder,extensions=None):
        # find files in a subfolder with an extension
        folders = [fold[0] for fold in os.walk(folder)]
        files = [fl+'/'+fn for fl in folders for fn in os.listdir(fl)]
        if extensions:
            files = [fn for fn in files if (any('.'+ext in fn for ext in extensions))]
        return files

    def sort_by_list(input,rank_list,reverse=False):
        # return list sorted by another list
        sort_flip = -1 if reverse else 1
        arr1 = numpy.array(input)
        arr2 = numpy.array(rank_list)
        sorted_list = arr1[arr2.argsort()[::sort_flip]].tolist()
        return sorted_list
