### LAYOUT OBJECTS ###
from common import *
from media import *
from plotting import *
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

    def add_neighbors(self,height,width,CSM:CoordinateSystem):
        # add positions of cells that border this cells
        #x,y = self.position
        self.neighbors = CSM.neighbors(self.position)

        #directions = {'up':(0,-1),
        #              'down':(0,1),
        #              'left':(-1,0),
        #              'right':(1,0)}
        #for d in directions:
        #    x1 = x+directions[d][0]
        #    y1 = y+directions[d][1]
        #    if ((x1 >= 0) & (x1 < height) & (y1 >= 0) & (y1 < width)):
        #        self.neighbors += [(x1,y1)]


class Grid:
    # collection of cells with bridges and tautness
    # bridge: the connection between neighbor cells
    # tautness: the sum of strengths across all bridges
    def __init__(self,height:int,width:int=0,width2:int=0,angle=False,distance_weight=0,angle_weight=0,
                 coordinate_system=CoordinateSystem()):
        if width == 0:
            width = height
        self.height = height
        self.width = width
        self.width2 = width2 if width2 > 0 else width
        self.dimensions = (height,width)
        self.size = height*width
        self.cells = {}
        self.blocked = []
        self.center = None

        self.angle = angle

        self.distance_weight = distance_weight
        self.angle_weight = angle_weight

        self.CS = coordinate_system
        self.CSM = CoordinateSystem(self.CS.lattice,self.dimensions)

        self.positions = self.CSM.get_positions()

        self.max_distance = self.CS.distance((self.height,self.width))
        
        for position in self.positions:
            self.cells[position] = None

    def __repr__(self):
        string = ''
        for p in self.positions:
            if self.cell_filled(p):
                string += '{}'.format(self.cells[p].picture.color)
            else:
                string += '{}'.format(Color(0,0,0))
            string += ' || '
        string += '\n'
        return string[:-1]

    def copy_grid(self):
        # copy grid
        grid = copy.deepcopy(self)
        return self

    def _safe_cells(self):
        # returns unblocked cells that have images
        safe_cells = [cell for cell in self.cells if cell not in self.blocked]
        return safe_cells

    def cell_filled(self,position):
        # check if a cell already has a picture
        filled = (self.cells[position] is not None) | (position in self.blocked)

        return filled

    def _get_order(self,corner=None):
        # return list of possible cells to insert based on target
        closed_positions = [cell for cell in self.cells if self.cell_filled(cell)]
        open_positions = sorted([(i,j) for i,j in self.positions if (i,j) not in closed_positions])
        if corner:
            R,theta = corner
            x,y = self.CS.from_polar(R,theta)
            target = self.CSM.to_matrix(R,theta)

            #target = (corner[0]*(self.height-1),corner[1]*(self.width-1))
            distances = [self.CS.distance(position,target) for position in open_positions]

            open_positions = Common.sort_by_list(open_positions,distances)
        else:
            target = None

        if len(open_positions)>0:
            position = open_positions[0]
        else:
            position = None
        return position,target

    def add_cell(self,picture:Picture,corner=None):
        # add a picture to a cell or the closest open position
        position,target = self._get_order(corner)      
        if position:
            x,y = position

            cell = Cell(picture,(x,y))
            self.cells[(x,y)] = cell
      
            self.cells[(x,y)].add_neighbors(self.height,self.width,self.CSM)
            self.cells[(x,y)].picture.target = target

    def add_center(self,center_size=1,blocked=None):
        # block off space in the center of the grid for a larger central image
        # height and width should both be odd or even together
        # need to round center_size to be odd or even too
        # ensure a buffer between the center and the sides of the grid
        ## FUTURE: use CoordinateSystem to specifiy coordinate cells and use self.center
        if center_size > 0:
            if blocked is not None:
                self.blocked.extend(blocked)
            else:
                blocked_cells = self.CSM.get_positions(position=(self.height//2,self.width//2),
                                                       width=center_size)
                self.blocked.extend(blocked_cells)

    def add_from_gallery(self,gallery:Gallery):
        # add pictures from a gallery in a specific order
        self.angle = gallery.angle
        if gallery.center:
            center_xy = min(self.blocked) ## HEX??
            self.cells[center_xy] = Cell(gallery.center,center_xy)

        for picture in gallery.pictures:
            self.add_cell(picture,gallery.corners.get(picture.id))

        self.add_cell_strengths()

        return

    def send_to_gallery(self):
        # put all pictures back into a gallery
        if len(self.blocked):
            center_xy = min(self.blocked)
            center = self.cells[center_xy].picture
        else:
            center = None

        pictures = [self.cells[cell].picture for cell in self._safe_cells()]
        if center:
            pictures.append(center)

        gallery = Gallery(pictures,randomize=False,center=center)
        return gallery

    def reseed(self):
        # organize pictures by a color mapping
        gallery = self.send_to_gallery()
        
        gallery.order_pictures()
        grid = Grid(self.height,self.width,self.width2,distance_weight=self.distance_weight,angle_weight=self.angle_weight,
                    coordinate_system=self.CS)
        grid.add_center(blocked=self.blocked)
        grid.add_from_gallery(gallery)
        return grid

    def worst_pairings(self):
        # list of cells pairings by order of strengths
        combos = list(itertools.combinations(range(self.size - len(self.blocked)),2))
        products = [(i+1)*(j+1) for i,j in combos]
        pairings = Common.sort_by_list(combos,products)
        return pairings

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
            neighbors = [self.cells[neighbor] for neighbor in self.cells[cell].neighbors if neighbor not in self.blocked]
            region.extend([self.cells[cell]] + neighbors)
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
                R,theta = cell.picture.target
                x1,y1 = self.CSM.to_matrix(R,theta)
                ##x1,y1 = cell.picture.target
                distance_strength = self.CS.distance(cell.position,cell.picture.target)/self.max_distance

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
                angle_diff = CoordinateSystem.angle_difference(current_angle,angle+self.angle)
                angle_strength = angle_weight * angle_diff/(2*math.pi)
            else:
                angle_strength = 0.5
        else:
            angle_weight = 0
            angle_strength = 0

        # account for color difference
        difference_weight = 1 - sum([distance_weight,angle_weight])
        neighbors = [neighbor for neighbor in cell.neighbors if neighbor not in self.blocked]
        differences = [(cell.picture.difference(self.cells[neighbor].picture))**2 for neighbor in neighbors]
        difference_strength = difference_weight * (sum(differences) / len(neighbors))
        
        self.cells[(x0,y0)].strength = difference_strength + distance_strength + angle_strength

    def add_cell_strengths(self,region=None):
        # update all cell strengths
        if region:
            cells = [cell.position for cell in region]
        else:
            cells = [cell for cell in self.cells if cell not in self.blocked]
        for cell in cells:
            self.add_cell_strength(self.cells[cell])
       
    def worst_cells(self):
        # list cells in order of strength
        positions = self._safe_cells()
        strengths = [self.cells[c].strength for c in positions]
        worst = Common.sort_by_list(positions,strengths,reverse=True)
        worst = [tuple(w) for w in worst]
        return worst #,strengths

    def get_tautness(self):
        # find overall strength of grid
        # -1 = all cells different from neighbors
        # 0 = average cells half a color different
        # 1 = all cells same as neighbors
        safe_cells = self._safe_cells()
        taut_exp = sum([self.cells[cell].strength for cell in safe_cells])/len(safe_cells)
        taut = 1 - 2*taut_exp
        #taut = (exp**taut_exp-1)*(exp-1)
        return taut

    def save_output(self,dimension=50,library=None,
                    secondary_scale=None,vibrant=True,border=0,border_color=(0,0,0),
                    print_strength=False,capsize=10000):
        # create image file of cells
        # if library is not given, only print colors

        # extend grid and add border color
        border = min(border,dimension)

        if self.CS.lattice == 'hexagonal':
            hex,extra = self.CSM.scaling
            ex = extra if self.width==self.width2 else 0
            
            height_adj = math.ceil(self.height/2) + math.floor(self.height/2)/2 # +1 for odd rows, +1/2 for even rows
            width_max = max(self.width,self.width2) # base overall frame on bigger of two widths
            image_height = dimension*height_adj + border*hex*self.height #borders between rows are small, overall height is adjusted because rows fit together
            image_width = dimension*(width_max*hex+ex) + border*hex*width_max

        elif self.CS.lattice == 'cartesian':
            image_width = (dimension + border)*self.width
            image_height = (dimension + border)*self.height
    

        # prevent program from crashing by capping image size
        image_width = round(min(capsize,image_width))
        image_height = round(min(capsize,image_height))

        grid_image = Image.new('RGB',(image_width,image_height),border_color)

        center_block = min(self.blocked) if len(self.blocked) else None ## FUTURE: use CoordinateSystem
        
        for i,j in self.positions:
            if self.cells[(i,j)]:
                picture = self.cells[(i,j)].picture
                # expand the center image
                dim_mul = 1

                if (i,j) == center_block:
                    dim_mul = (max(self.blocked)[0] - min(self.blocked)[0] + 1)
                        
                paste_secondary = None
                if library is None:
                    if vibrant:
                        color = picture.color
                    else:
                        color = picture.greyscale

                    paste_picture = Image.new('RGB',(dimension*dim_mul,dimension*dim_mul),color.rgb)
                    
                    if (secondary_scale is not None) & (picture.secondary is not None):
                        secondary = picture.secondary
                        dimension_2 = int(dimension*min(0.5,secondary_scale))
                        dimension_2 = int(dimension*min(0.5,secondary_scale))
                        paste_secondary = Image.new('RGB',(dimension_2,dimension_2),secondary.rgb)
                        paste_picture.paste(paste_secondary,(int(dimension*0.5),int(dimension*0.5)))

                    if print_strength:
                        font_size = round(dimension/5)
                        font = ImageFont.truetype('arial.ttf',font_size) ### LINK SOMEWHERE
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
                    dim_resize = dimension*dim_mul + border*(dim_mul-1)
                    paste_picture = paste_picture.resize((dim_resize,dim_resize),Image.ANTIALIAS)

                if self.CS.lattice == 'hexagonal':
                    paste_picture = Shaper.shape(paste_picture,'hexagon')
                    paste_mask = paste_picture
                    d_p = (1-hex)*dimension
                    j_p,i_p = self.CS.to_rectangular((j,i))
                else:
                    paste_mask = None
                    d_p = 0
                    i_p,j_p = i,j

                paste_box = (int(dimension*j_p + border*(j_p+0.5)-j_p*d_p),
                             int(dimension*i_p + border*(i_p+0.5)-i_p*d_p),
                             int(dimension*(j_p+dim_mul) + border*(j_p+dim_mul-0.5)-j_p*d_p),
                             int(dimension*(i_p+dim_mul) + border*(i_p+dim_mul-0.5)-i_p*d_p))

                grid_image.paste(paste_picture,paste_box,paste_mask)
                #grid_image.save('C:\\Users\\mfran\\OneDrive\\Projects/mf_traveler_20181013/mosaics/test.png')

        if self.CS.lattice == 'hexagonal':
            grid_image = Shaper.blot(grid_image)
        
        return grid_image