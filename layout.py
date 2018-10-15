### LAYOUT OBJECTS ###
from common import *
from media import *
import itertools

class Cell:
    # basic unit of a grid with picture, position, neighbors and strength
    # position: (x,y) within grid
    # neighbors: cells that border this cell
    # strength: a measure of how distant the prominent color of this cell is to its neighbors
    def __init__(self,picture:Picture,position):
        self.picture = picture
        self.position = position
        self.neighbors = []
        self.strength = 0

    def add_neighbors(self,height,width):
        # add positions of cells that border this cells
        x,y = self.position
        directions = {'up':(0,-1),
                      'down':(0,1),
                      'left':(-1,0),
                      'right':(1,0)}
        for d in directions:
            x1 = x+directions[d][0]
            y1 = y+directions[d][1]
            if ((x1 >= 0) & (x1 < height) & (y1 >= 0) & (y1 < width)):
                self.neighbors += [(x1,y1)]

class Grid:
    # collection of cells with bridges and tautness
    # bridge: the connection between neighbor cells
    # tautness: the sum of strengths across all bridges
    def __init__(self,height:int,width:int=0,exp=1,account_for_angle=False,angle=False):#,outputs=[],finalized=False):
        if width == 0:
            width = height
        self.height = height
        self.width = width
        self.size = height*width
        self.cells = {}
        self.bridges = {}
        self.strengths = []
        self.exp = exp
        self.account_for_angle=account_for_angle
        self.angle = angle
        
        for i in range(height):
            for j in range(width):
                self.cells[(i,j)] = None

    def __repr__(self):
        string = ''
        for i in range(self.height):
            for j in range(self.width):
                if self.cell_filled((i,j)):
                    string += '{}'.format(self.cells[(i,j)].picture.color)
                else:
                    string += '{}'.format(Color(0,0,0))
                string += ' || '
            string += '\n'
        return string[:-1]

    def cell_filled(self,position):
        # check if a cell already has a picture
        filled = False
        if self.cells[position] is not None:
            filled = True
        return filled

    def get_order(self,position):
        # return list of possible cells to insert based on target
        if not position:
            flip = True
            x = self.height//2
            y = self.width//2
        else:
            flip = False
            x = round(position[0]*(self.height-1))
            y = round(position[1]*(self.width-1))
        
        positions = [(x,y)]

        n_max = max(2*self.height,2*self.width)
        for n in range(1,n_max):
            x_inc = -n
            y_inc = 0
            x_move = 1
            y_move = 1
            for m in range(n*4):
                x_new = x+x_inc
                y_new = y+y_inc
                if (x_new >= 0) & (x_new < self.height) & (y_new >= 0) & (y_new < self.width):
                    positions += [(x_new,y_new)]
                x_inc += x_move
                y_inc += y_move
                if abs(x_inc) == n:
                    x_move *= -1
                if abs(y_inc) == n:
                    y_move *= -1
        if flip:
            positions.reverse()

        return positions 

    def add_cell(self,picture:Picture,corner=None):
        # add a picture to a cell or the closest open position
        cell_available = False
        if corner is None:
            # find first empty cell
            n = 0
            while (not cell_available) & (n < self.size):
                x = (n)//self.width
                y = (n)%self.width
                if (not self.cell_filled((x,y))):
                    cell_available = True
                    position = (x,y)
                n += 1
        else:
            # get closest to desitnation
            positions = self.get_order(corner)
            pos = 0
            while (not cell_available) & (pos < len(positions)):
                position_try = (positions[pos][0],positions[pos][1])
                if (not self.cell_filled(position_try)):
                    cell_available = True
                    position = position_try
                pos += 1
                   
        if cell_available:
            x,y = position
            self.cells[(x,y)] = Cell(picture,(x,y))
            self.cells[(x,y)].add_neighbors(self.height,self.width)
            self.add_bridges(self.cells[(x,y)])

    def add_from_gallery(self,gallery:Gallery):
        # add pictures from a gallery in a specific order
        self.angle = gallery.angle
        for picture in gallery.pictures:
            self.add_cell(picture,gallery.corners.get(picture.id))
        return

    def send_to_gallery(self):
        # put all pictures back into a gallery
        gallery = Gallery([self.cells[cell].picture for cell in self.cells],randomize=False)
        return gallery

    def reseed(self,corners):
        # organize pictures by a color mapping
        gallery = self.send_to_gallery()
        gallery.order_pictures(corners)
        grid = Grid(self.height,self.width,exp=self.exp,account_for_angle=corners.get('account for angle',False))
        grid.add_from_gallery(gallery)
        return grid

    def worst_pairings(self):
        # list of cells pairings by order of strengths
        combos = list(itertools.combinations(range(self.size),2))
        products = [(i+1)*(j+1) for i,j in combos]
        pairings = sort_by_list(combos,products)
        return pairings

    def swap_pictures(self,cells1,cells2):
        # move pictures between two cells
        n_cells = len(cells1)
        for c in range(n_cells):
            temp_picture = self.cells[cells1[c]].picture
            self.cells[cells1[c]].picture = self.cells[cells2[c]].picture
            self.cells[cells2[c]].picture = temp_picture

        for c in range(n_cells):
            self.add_bridges(self.cells[cells1[c]])
            self.add_bridges(self.cells[cells2[c]])

        for c in range(n_cells):
            self.add_cell_strength(self.cells[cells1[c]])
            self.add_cell_strength(self.cells[cells2[c]])

    def difference(self,cell1,cell2):
        # find distance between colors of pictures in two cells
        distance = self.cells[cell1].picture.difference(self.cells[cell2].picture)
        return distance

    def add_cell_strength(self,cell,angle_penalty=256**2):
        # recalculate strength metric based on bridges
        x0,y0 = cell.position

        angle = cell.picture.angle

        if (angle is not None) & self.account_for_angle:
            current_angle = math.atan2(y0-self.width/2,x0-self.height/2)
            angle_strength = angle_penalty * angle_difference(current_angle,angle_simplified(angle+self.angle))
        else:
            angle_strength = 0

        self.cells[(x0,y0)].strength = \
            sum([self.bridges.get((min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1)),0) for (x1,y1) in cell.neighbors])\
            * (4/len(cell.neighbors)) + angle_strength

    def add_bridges(self,cell):
        # add connection between neighbor cells
        x0,y0 = cell.position

        if self.cell_filled((x0,y0)):
            picture0 = self.cells[(x0,y0)].picture
            for (x1,y1) in cell.neighbors:
                if self.cell_filled((x1,y1)):
                    picture1 = self.cells[x1,y1].picture
                    self.bridges[(min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1))] = picture0.difference(picture1)**self.exp

            for (x1,y1) in [(x0,y0)]+cell.neighbors:
                if self.cell_filled((x1,y1)):
                    self.add_cell_strength(self.cells[(x1,y1)])
        
    def get_tautness(self):
        # find overall strength of grid
        taut = 0

        for b in self.bridges:
            taut += self.bridges[b]
        return taut

    def sort_strengths(self):
        # list cells in order of strength
        cell_positions = list(self.cells.keys())
        cell_strengths = [self.cells[c].strength for c in self.cells]
        strengths_sorted = sorted(cell_strengths,reverse=True)
        self.strengths = []
        for strength in strengths_sorted:
            s = cell_strengths.index(strength)
            self.strengths += [cell_positions[s]]
            cell_positions.pop(s)
            cell_strengths.pop(s)

    def worst_cell(self,n=0):
        # find the nth worst performing cell
        self.sort_strengths()
        cell = self.strengths[n]
        strength = self.cells[cell].strength
        return cell,strength

    def save_output(self,folder='',name='interval',extension='jpg',dimension=50,
                    library=None,secondary_scale=None,vibrant=True,display=False,border=0,border_color=(0,0,0)):
        # print image file of cells
        # if library is not given, only print colors

        # extend grid and add border color
        border = min(border,dimension)

        grid_image = Image.new('RGB',((dimension+border)*self.width,
                                      (dimension+border)*self.height),border_color)

        for i in range(self.height):
            for j in range(self.width):
                picture = self.cells[(i,j)].picture
                paste_secondary = None
                if library is None:
                    if vibrant:
                        color = picture.color
                    else:
                        color = picture.greyscale
                    paste_picture = Image.new('RGB',(dimension,dimension),color.rgb)
                    if (secondary_scale is not None) & (picture.secondary is not None):
                        secondary = picture.secondary
                        dimension_2 = int(dimension*min(0.5,secondary_scale))
                        paste_secondary = Image.new('RGB',(dimension_2,dimension_2),secondary.rgb)
                else:
                    paste_picture = library.get_photo(picture.id).image
                    h,w = paste_picture.size
                    if h != w:
                        m = min(h,w)/2
                        paste_picture = paste_picture.crop((int(h/2-m),int(w/2-m),int(h/2+m),int(w/2+m)))

                    paste_picture = paste_picture.resize((dimension,dimension),Image.ANTIALIAS)
                grid_image.paste(paste_picture,(int(dimension*j + border*(j+0.5)),
                                                int(dimension*i + border*(i+0.5)))) #### EXTEND FOR BORDER

                if paste_secondary is not None:
                    grid_image.paste(paste_secondary,(int((dimension+border)*(j+0.5)),
                                                      int((dimension+border)*(i+0.5))))
        
        if display == 'show':
            grid_image.show()
        elif display == 'save':
            grid_image.save('{}/{}.{}'.format(folder,name,extension))

    def strength_value(tautness,size,power=0.5,min_taut=5.5,max_taut=20):
        strength = 1/(1+min(max_taut,max(math.sqrt(tautness)/size,min_taut))**power-min_taut**power)
        return strength