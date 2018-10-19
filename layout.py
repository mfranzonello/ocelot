### LAYOUT OBJECTS ###
from common import *
from media import *
import itertools
from PIL import ImageDraw,ImageFont
import copy

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
    def __init__(self,height:int,width:int=0,angle=False,distance_weight=0,angle_weight=0):
        if width == 0:
            width = height
        self.height = height
        self.width = width
        self.size = height*width
        self.cells = {}

        self.angle = angle

        self.distance_weight = distance_weight
        self.angle_weight = angle_weight
        
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

    def copy_grid(self):
        grid = copy.deepcopy(self)
        return self

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
            x = round(self.height/2)
            y = round(self.width/2)
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
            target = None
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
            target = positions[0]
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
            self.cells[(x,y)].picture.target = target

    def add_from_gallery(self,gallery:Gallery):
        # add pictures from a gallery in a specific order
        self.angle = gallery.angle
        for picture in gallery.pictures:
            self.add_cell(picture,gallery.corners.get(picture.id))
        self.add_cell_strengths()

        return

    def send_to_gallery(self):
        # put all pictures back into a gallery
        gallery = Gallery([self.cells[cell].picture for cell in self.cells],randomize=False)
        return gallery

    def reseed(self,distance_weight=0,angle_weight=0):
        # organize pictures by a color mapping
        gallery = self.send_to_gallery()
        gallery.order_pictures()
        grid = Grid(self.height,self.width,distance_weight=distance_weight,angle_weight=angle_weight)
        grid.add_from_gallery(gallery)
        return grid

    def worst_pairings(self):
        # list of cells pairings by order of strengths
        combos = list(itertools.combinations(range(self.size),2))
        products = [(i+1)*(j+1) for i,j in combos]
        pairings = sort_by_list(combos,products)
        return pairings

    def _rms_change(self,original,delta):
        change = delta * (2*original + delta)
        return change

    def check_swap(self,cell1,cell2,threshold=0):
        # check to see if a swap is worthwhile
        
        strength_0 = self.get_tautness()
        self.swap_pictures(cell1,cell2)
        strength_1 = self.get_tautness()

        if strength_1 - strength_0 > threshold:
            # keep swap and tell sorter to move on
            swap = True
        else:
            # undo swap and tell sorter to try next pairing
            self.swap_pictures(cell1,cell2)
            swap = False

        return swap

    def swap_pictures(self,cell1,cell2):
        # move pictures between two cells
        temp_picture = self.cells[cell1].picture
        self.cells[cell1].picture = self.cells[cell2].picture
        self.cells[cell2].picture = temp_picture
        region = []
        for cell in cell1,cell2:
            region.extend([self.cells[cell]] + [self.cells[neighbor] for neighbor in self.cells[cell].neighbors])
        self.add_cell_strengths(region=region)

    def difference(self,cell1,cell2):
        # find distance between colors of pictures in two cells
        distance = self.cells[cell1].picture.difference(self.cells[cell2].picture)
        return distance

    def add_cell_strength(self,cell):
        # recalculate strength metric based on bridges
        x0,y0 = cell.position

        # account for placement distance
        if (self.distance_weight > 0):
            distance_weight = self.distance_weight
            if cell.picture.target is not None:
                x1,y1 = cell.picture.target
                distance_strength = math.sqrt((x0 - x1)**2 + (y0 - y1)**2) / math.sqrt(self.height**2 + self.width**2)
            else:
                distance_strength = 0.5
        else:
            distance_weight = 0
            distance_strength = 0

        # account for placement angle
        if self.angle_weight > 0:
            if cell.picture.angle is not None:
                angle = cell.picture.angle
                angle_weight = self.angle_weight
                current_angle = math.atan2(y0-self.width/2,x0-self.height/2)
                angle_diff = angle_difference(current_angle,angle_simplified(angle+self.angle))
                angle_strength = angle_weight * angle_diff/(2*math.pi)
            else:
                angle_strength = 0.5
        else:
            angle_weight = 0
            angle_strength = 0

        # account for color difference
        difference_weight = 1 - sum([distance_weight,angle_weight])
        differences = [(cell.picture.difference(self.cells[neighbor].picture))**2 for neighbor in cell.neighbors]
        difference_strength = difference_weight * (sum(differences) / len(cell.neighbors))
        
        self.cells[(x0,y0)].strength = difference_strength + distance_strength + angle_strength

    def add_cell_strengths(self,region=None):
        # update all cell strengths
        if region:
            cells = [cell.position for cell in region]
        else:
            cells = self.cells
        for cell in cells:
            self.add_cell_strength(self.cells[cell])
       
    def get_tautness(self):
        # find overall strength of grid
        # -1 = all cells different from neighbors
        # 0 = average cells half a color different
        # 1 = all cells same as neighbors
        taut = 1-2*sum([self.cells[cell].strength for cell in self.cells])/self.size
        return taut

    def worst_cells(self):
        # list cells in order of strength
        positions = list(self.cells.keys())
        strengths = [self.cells[c].strength for c in self.cells]
        worst = sort_by_list(positions,strengths,reverse=True)
        worst = [tuple(w) for w in worst]
        return worst #,strengths

    def save_output(self,dimension=50,library=None,
                    secondary_scale=None,vibrant=True,border=0,border_color=(0,0,0),
                    print_strength=False):
        # create image file of cells
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
                        paste_picture.paste(paste_secondary,(int(dimension*0.5),int(dimension*0.5)))

                    if print_strength:
                        font_size = round(dimension/5)
                        font = ImageFont.truetype('C:/Windows/Fonts/Arial.ttf',font_size)
                        strength_text = '{:.03f}'.format(self.cells[(i,j)].strength)
                        target_text = '{}'.format(self.cells[(i,j)].picture.target)
                        rgb_text = '({},{},{})'.format(*self.cells[(i,j)].picture.color.rgb)

                        texts = [strength_text,target_text,rgb_text]
                        draw = ImageDraw.Draw(paste_picture)

                        for text in texts:
                            draw.text((0,texts.index(text)*(font_size+1)),text,(255,255,255),font=font)
                        paste_picture = draw.im

                else:
                    paste_picture = library.get_photo(picture.id).image
                    h,w = paste_picture.size
                    if h != w:
                        m = min(h,w)/2
                        paste_picture = paste_picture.crop((int(h/2-m),int(w/2-m),int(h/2+m),int(w/2+m)))

                    paste_picture = paste_picture.resize((dimension,dimension),Image.ANTIALIAS)

                paste_box = (int(dimension*j + border*(j+0.5)),
                             int(dimension*i + border*(i+0.5)),
                             int(dimension*(j+1) + border*(j+0.5)),
                             int(dimension*(i+1) + border*(i+0.5)))
                grid_image.paste(paste_picture,paste_box)
        
        return grid_image