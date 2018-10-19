### OPTIMIZATION OBJECTS ###
from common import *
from coloring import *
from media import *
from layout import *
from structure import *
import copy

class Engine:
    def __init__(self,printer:Printer,print_gif=False):
        self.grid = None
        self.printer = printer
        self.print_gif = print_gif

    def store_grid(self,dimension=50,full=False,extension='jpg'):
        self.printer.store_grid(self.grid,full=full)

    def get_grid(self):
        grid = copy.deepcopy(self.grid)
        return grid

    def get_strength(self):
        if self.grid is None:
            strength = None
        else:
            strength = self.grid.get_tautness()
        return strength

class Assembler(Engine):
    def __init__(self,collector:Collector,printer:Printer,name='',square=False,secondary_scale=None,
                 distance_weight=0,angle_weight=0,print_gif=True):
        Engine.__init__(self,printer,print_gif=print_gif)      
        print('Setting up grid...')

        gallery = collector.get_gallery()
        height,width = self._best_fit(gallery.size,square)
        print(' ...using {} of {} images for {}x{} grid'.format(height*width,gallery.size,height,width))
        
        self.grid = Grid(height,width,distance_weight=distance_weight,angle_weight=angle_weight)
        self.grid.add_from_gallery(gallery)

        if self.print_gif:
            self.store_grid(full=True)
            self.store_grid()

    def _best_fit(self,n_pics,square=False):
        height = width = int(math.sqrt(n_pics))
        if not square:
            sqr = round(math.sqrt(n_pics))
            sqr_dn = round(math.sqrt(n_pics)*(1-0.1))
            sqr_up = round(math.sqrt(n_pics)*(1+0.1))

            sizes = list(itertools.product(range(sqr_dn,sqr+1),range(sqr,sqr_up+1)))
            deviations = [n_pics-i*j for i,j in sizes]
            if len(deviations)>0:
                height,width = sizes[deviations.index(min([d for d in deviations if d>=0]))]
        return height,width

class Sorter(Engine):
    def __init__(self,assembler:Assembler,print_after=1000):
        Engine.__init__(self,assembler.printer,assembler.print_gif)
        self.grid = assembler.get_grid()

        self.n_trials = 0
        self.print_after = print_after

    def reseed(self):
        print('\nSeeding grid...')
        taut_0 = self.grid.get_tautness()
        grid = self.grid.reseed()
        self.grid = grid
        taut_1 = self.grid.get_tautness()
        print(' ...{:0.2%} to {:0.2%} strength'.format(taut_0,taut_1))

        if self.print_gif:
            self.store_grid()
        return self.grid

    def swap_worst(self,threshold=0,trials=1):
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
                        if (n - swap_last >= self.print_after) | (pair == len(pairings)):
                            exhausted = True

                    if (not n%self.print_after) & self.print_gif:
                        self.store_grid()

                    if n == trials:
                        exhausted = True

        except KeyboardInterrupt:
            pass

        self.n_trials = n
        if (n%self.print_after) & self.print_gif:
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