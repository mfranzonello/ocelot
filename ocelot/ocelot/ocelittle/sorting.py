### OPTIMIZATION OBJECTS ###
from common import *
from coloring import *
from media import *
from layout import *
from structure import *
import copy

class Engine:
    # object that can create or make changes to a grid
    def __init__(self,printer:Printer):
        self.grid = None
        self.printer = printer
        self.project = printer.project

        self.coordinate_system = printer.project.coordinate_system
        self.coordinate_matrix = None

        self.n_trials = 0

    def store_grid(self,dimension=50,full=False,extension='jpg'):
        # add a grid to the print queue
        self.printer.store_grid(self.grid,full=full)

    def get_strength(self):
        # get result of grid strength for summary
        if self.grid is None:
            strength = None
        else:
            strength = self.grid.get_tautness()
        return strength
        
    def assemble(self,collector:Collector):
        # put together images in initial grid layout
        print('Setting up grid...')
      
        gallery = collector.get_gallery()
        # if the gallery didn't turn up a center image, then don't pass center
        center_size = self.project.profile_size if gallery.center else 0

        height,width,width2,center_size = self._best_fit(gallery.size,self.project.grid_aspect,center_size=center_size)

        # add dimensions to the CS
        matrix = (height,width) if width2 == 0 else (height,width,width2)
        self.coordinate_matrix = self.coordinate_system.make_matrix(matrix)

        n_total = self.coordinate_matrix.n_total()
        center_total = self.coordinate_matrix.ring_size(width=center_size)
        used = int(n_total - center_total + (center_size>0))
        print(' ...using {} of {} images for {}x{} grid'.format(used,gallery.size,height,max(width,width2)))
        
        self.grid = Grid(height,width,width2,weights=self.project.weights,
                         coordinate_system=self.coordinate_system)
        self.grid.add_center(center_size=center_size)
        self.grid.add_from_gallery(gallery)

        if self.project.grid_gif:
            self.store_grid(full=True)
            self.store_grid()

    def _best_fit(self,n_pics,aspect=None,center_size=0,odd=None):
        # find the grid size that can fit a center if present with best ratio
        # an even width means the center must also be even
        # an odd width means the center must also be odd

        width2 = 0
        ## ADD SPECIAL CASE FOR HEXAGONAL COORDINATES WITH WIDTH2 BEING ODD ROWS

        # if a center size is given, find if even or odd sizing is better
        if center_size > 0:
            center_size_even = round((center_size)/2)*2
            center_size_odd = round((center_size-1)/2)*2+1
            n_pics_even = n_pics + center_size_even**2
            n_pics_odd = n_pics + center_size_odd**2
            height_even,width_even,_,_ = self._best_fit(n_pics_even,aspect=aspect,odd=False)
            height_odd,width_odd,_,_ = self._best_fit(n_pics_odd,aspect=aspect,odd=True)

            deviations_even = n_pics_even - height_even*width_even
            deviations_odd = n_pics_odd - height_odd*width_odd
            
            if self.coordinate_system.lattice == 'cartesian':
                if deviations_even < deviations_odd:
                    height,width,center_size = height_even,width_even,center_size_even
                else:
                    height,width,center_size = height_odd,width_odd,center_size_odd
            elif self.coordinate_system.lattice == 'hexagonal':
                height,width,center_size = height_odd,width_odd,center_size_odd

        # no center size given or center size added to n_pics for recursion
        else:
            if aspect:
                aspect = self.coordinate_system.convert_aspect(aspect)
                aspect_ratio = aspect[0]/aspect[1]
                # square aspect ratio
                # only way that works is square root
                if aspect_ratio == 1:
                    height = width = int(math.sqrt(n_pics))
                else:
                    # specified aspect ratio
                    # check which way of rounding height and width gives the best fit
                    height_up = math.ceil(math.sqrt(n_pics*aspect_ratio))
                    width_up = math.floor(n_pics/height_up)

                    height_down = math.floor(math.sqrt(n_pics*aspect_ratio))
                    width_down = math.floor(n_pics/height_up)

                    deviations_down = abs(aspect_ratio - height_down/width_down)
                    deviations_up = abs(aspect_ratio - height_up/width_up)

                    if odd is not None:
                        if width_down%2+1 == odd:
                            height,width = height_down,width_down
                        else:
                            height,width = height_up,width_up
                    else:
                        if deviations_down < deviations_up:
                            height,width = height_down,width_down
                        else:
                            height,width = height_up,width_up

            # no specified aspect ratio
            # start with a square aspect ratio and move with 10% in either direction
            else:
                height = width = int(math.sqrt(n_pics))

                sqr = round(math.sqrt(n_pics))
                sqr_dn = round(math.sqrt(n_pics)*(1-0.1))
                sqr_up = round(math.sqrt(n_pics)*(1+0.1))

                range1 = range(sqr_dn,sqr+1)
                range2 = range(sqr,sqr_up+1)
                if odd is not None: # make width odd or even
                    range2 = [r for r in range2 if r%2 == odd]
                sizes = list(itertools.product(range1,range2))

                deviations = [n_pics-i*j for i,j in sizes]
                if len(deviations)>0:
                    height,width = sizes[deviations.index(min([d for d in deviations if d>=0]))]

        return height,width,width2,center_size

    def reseed(self):
        # place pictures according to coloring
        print('\nSeeding grid...')
        taut_0 = self.grid.get_tautness()
        grid = self.grid.reseed()
        self.grid = grid

        taut_1 = self.grid.get_tautness()
        print(' ...{:0.2%} to {:0.2%} strength'.format(taut_0,taut_1))

        if self.project.grid_gif:
            self.store_grid()
        return self.grid

    def swap_worst(self,threshold=0,trials=1):
        # swap cells with the worst strength and iterate
        print('\nOptimizing grid...')
        n = 0
        exhausted = False
        taut_0 = self.grid.get_tautness()
        swap_last = 0

        grid = self.grid.copy_grid()
        pairings = self.grid.worst_pairings()
        try:
            self._update_trial(n)
            while (not exhausted):
                worst = self.grid.worst_cells()
                pair = 0
                move_on = False

                while (not move_on) & (pair < len(pairings)) & (not exhausted):
                    n += 1
                    
                    cells = worst[pairings[pair][0]],worst[pairings[pair][1]]
                    cell1 = cells[0]
                    cell2 = cells[1]

                    swap = grid.check_swap(cell1,cell2)

                    if swap:
                        taut_1 = grid.get_tautness()
                        swap_last = n
                        self._update_trial(n,taut_1)
                        move_on = True
                    else:
                        self._update_trial(n)
                        pair += 1
                        if (n - swap_last >= self.project.print_after) | (pair == len(pairings)):
                            exhausted = True

                    if (not n%self.project.print_after) & self.project.grid_gif:
                        self.store_grid()

                    if n == trials:
                        exhausted = True

        except KeyboardInterrupt:
            pass

        self.n_trials = n
        if (n%self.project.print_after) & self.project.grid_gif:
            self.store_grid()

        print()
        self.grid = grid
        return grid

    def finalize(self):
        # put final arrangement in printer
        self.store_grid(full=True)

    def _update_trial(self,n,taut=None):
        # update on trial and result
        improve_text = ' | strength: '
        if taut is not None:
            spaces = ' '  if taut < 1 else ''
            improvement = '{}{:0.2%}{}'.format(improve_text,taut,spaces)
        else:
            spaces = ' '*(len(improve_text)+len('100.0%'))
            improvement = ''
        print(' Trial {}{}'.format(n,improvement,spaces),end='\r')

#    def _swap_cells(self,position1,position2):
#        # move two cells
#        print(' Switching cells {} and {}'.format(position1,position2))
#        self.grid.swap_pictures(position1,position2)

#    def _check_position(self,position):
#        # check if input is a cell in grid
#        check = False
#        if type(position) is tuple:
#            check = (position in self.grid._safe_cells())
#        return check

#    def ask_to_swap(self):
#        # prompt to pick cells to switch
#        move_on = False
#        positions = []
#        while not move_on:
#            position = input(' Enter {} cell by \'(x,y)\' position (or type \'quit\' to exit): '.format(['first','second'][len(positions)]))
#            if any(position.lower() == q for q in ['q','quit']):
#                move_on = True
#            elif self._check_position(position):
#                positions.append(position)
#            if len(positions) == 2:
#                move_on = True
#        if len(positions) == 2:
#            self.swap_cells(positions[0],positions[1])

#    def ask_user(self):
#        # ask the user to swap cells
#        move_on = False
#        while not move_on:
#            ask = input(' Do you want to swap cells or finish?')