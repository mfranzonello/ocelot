### PLOTTING OBJECTS ###
import math

class CoordinateSystem:
    def __init__(self,lattice=None,matrix=False,even=False,orientation=None):
        # cartesian: (x,y)
        # hexagonal: (x,y,z=-(x+y))
        lattices = {'cartesian': {'sides':4,
                                  'coordinates':2,
                                  'adjustments':[(0,-1,0,1),
                                                 (1,0,-1,0)], # N, W, S, E
                                  'directions':[(1,0), # +x
                                                (0,1), # +y
                                                (-1,0), # -x
                                                (0,-1), # -y
                                                (1,1), # +x,+y
                                                (-1,1), # -x,+y
                                                (-1,-1), # -x,-y
                                                (1,-1)]}, # +x,-y

                    'hexagonal': {'sides':6,
                                  'coordinates':3,
                                  'adjustments':[(-1,-1,0,1,1,0),
                                                 (1,0,-1,-1,0,1)], # NW, W, SW, SE, E, NE
                                  'directions':[(1,0), # +x
                                                (0,1), # +y
                                                (1,-1), # +z
                                                (-1,0), # -x
                                                (0,-1), # -y
                                                (-1,1)], # -z
                                  'scaling':(math.sqrt(3)/2,0.5)}}

        if lattice not in lattices:
            lattice = 'cartesian'
        self.lattice = lattice
        self.matrix = matrix # (h,w) for cartesian; (h,w) or (h,w_0,w_1) for hexagonal

        self.even = even
        self.orientation = orientation # hex: NS or EW; cart: even or odd

        self.sides = lattices[lattice]['sides']
        self.coordinates = lattices[lattice]['coordinates']
        self.adjustments = lattices[lattice]['adjustments']
        self.directions = lattices[lattice]['directions']

        self.scaling = None
        if self.lattice == 'hexagonal':
            hex,extra = lattices[lattice]['scaling']
            if self.matrix and (self.matrix[1] != self.matrix[-1]):
                ex = 0
            self.scaling = (hex,extra)

    def make_matrix(self,matrix):
        # make a matrix with the basics of this coordinate system
        return CoordinateSystem(lattice=self.lattice,matrix=matrix,even=self.even,orientation=self.orientation)

    def distance(self,position1,position2=(0,0)):
        # distance between coordinates on a cartestian mapping
        if self.lattice == 'hexagonal':
            positions = [(*p,-(p[0]+p[1])) for p in [position1,position2]] # z = -(x+y)
            adj = math.sqrt(2)
        else:
            positions = [position1,position2]
            adj = 1

        d = math.sqrt(sum([(positions[0][p]-positions[1][p])**2 for p in range(self.coordinates)]))/adj
        return d

    def _n_in_side(self,ring):
        # number in a side at nth ring
        if self.lattice == 'cartesian':
            n_in = 2*ring - self.even
        elif self.lattice == 'hexagonal':
            n_in = ring
        return n_in

    def _ring_start(self,ring):
        # starting n for a ring
        adj = 0
        if ring < 1:
            start = 0
        else:
            start = sum([self._n_in_side(r)*self.sides for r in range(self.even,ring)])
        return start

    def _position_to_ring(self,position):
        # given (x,y) return ring
        ring = math.ceil(self.distance((0,0),position))
        return ring

    def _n_to_ring(self,n):
        # given vertex return ring
        if (self.lattice == 'cartesian') & self.even:
            ring = math.ceil(math.sqrt(n/self.sides)) # (R*(R+1)/2 + (R-1)*R/2) * S = n_start
        else:
            if self.lattice == 'cartesian':
                adj = 2
            elif self.lattice == 'hexagonal':
                adj = 1
            ring = math.ceil((-1+math.sqrt(1-4*(-2*n/(adj*self.sides))))/2) # R*(R+1)/2 * S = n_start

        return ring

    def n_to_position(self,n):
        # given vertex return (x,y)
        position = None
        if n >= (0 + self.even):
            # matrix layout
            if self.matrix:
                if n < self.matrix[0] * self.matrix[1]:
                    if self.lattice == 'cartesian':
                        position = (n//self.matrix[1],n%self.matrix[1])
                    elif self.lattice == 'hexagonal':
                        position = (n//self.matrix[1],n%self.matrix[1]-(n//self.matrix[1])//2)
            
            # circular layout
            else:
                # first position is center
                if n == 0:
                    position = (0,0)
                # other positions are based on rings and sides
                else:
                    ring = self._n_to_ring(n) # which ring
                    n_in_side = self._n_in_side(ring) # how many in each ring side
                    in_ring = n - self._ring_start(ring) - 1 # how many past the start of the ring

                    side = in_ring // n_in_side # which side is n on
                    in_side = in_ring % n_in_side # how deep into side

                    # adjust around sides
                    x_side_adj = sum([self.adjustments[0][k]*n_in_side for k in range(len(self.adjustments[0])) if k < side])
                    x_in_side_adj = self.adjustments[0][side]*in_side
                    y_side_adj = sum([self.adjustments[1][k]*n_in_side for k in range(len(self.adjustments[1])) if k < side])
                    y_in_side_adj = self.adjustments[1][side]*in_side

                    # calculate position
                    if self.lattice == 'cartesian':
                        x_start = ring
                        y_start = -ring
                        if self.even:
                            x_start -= 0.5
                            y_start += 0.5
                    elif self.lattice == 'hexagonal':
                        x_start = ring
                        y_start = 0

                    x = x_start + x_side_adj + x_in_side_adj
                    y = y_start + y_side_adj + y_in_side_adj

                    position = (x,y)

        return position

    def position_to_n(self,position):
        # given (x,y) return vertex
        if self.matrix:
            if self.lattice == 'cartesian':
                n = position[0] * self.matrix[1] + position[1]
            elif self.lattice == 'hexagonal':
                n = position[0] * self.matrix[1] + position[1] -(position[0]//2)

        else:
            if position == (0,0):
                n = 0
            else:
                ring = self._position_to_ring(position)
                n_start = self._ring_start(ring)
                R,theta = self.to_polar(position)
                n_in_ring = max(1,self._n_in_side(ring) * self.sides)
                radians_per_n = 2*math.pi / n_in_ring
                n_inc = round(theta / radians_per_n)
                n = n_start + n_inc + 1
        
        return n

    def to_rectangular(self,position):
        # convert coordinates from any lattice to rectangular
        if self.lattice == 'cartesian':
            position_xy = position
        elif self.lattice == 'hexagonal':
            x = position[0]+position[1]*(0.5)
            y = 1.5*position[1]/math.sqrt(3)
            position_xy = (x,y)
        return position_xy

    def to_polar(self,position):
        # convert (x,y) to R,theta with theta in radians between 0 and 360 degrees
        R = self.distance(position,(0,0))
        cart_xy = self.to_rectangular(position)
        theta = math.atan2(cart_xy[1],cart_xy[0])
        if theta < 0:
            theta = 2*math.pi + theta
        return R,theta

    def from_polar(self,R,theta):
        # from polar to (x,y) coordinates
        if self.lattice == 'cartesian':
            x,y = R * math.cos(theta), R * math.sin(theta)

        elif self.lattice == 'hexagonal':
            phi,trident = CoordinateSystem.angle_hex(theta)

            # Trident I: x and y
            if trident == 1:
                x,y = R * math.cos(phi), R * math.sin(phi)
            # Trident II: z and x
            elif trident == 2:
                z,x = R * math.cos(phi), R * math.sin(phi)
                y = -(x+z)
            # Trident III: y and z
            elif trident == 3:
                y,z = R * math.cos(phi), R * math.sin(phi)
                x = -(y+z)

        return x,y

    def polar_to_matrix(self,R,theta):
        # convert corner on unit circle to position in matrix
        if self.matrix:
            x,y = self.in_matrix(self.from_polar(R,theta))
            return x,y

    def in_matrix(self,position,force=False,x_loc=0.5,y_loc=0.5):
        # transpose a position from a 0,0 center to a matrix
        x,y = position
        x = x+x_loc*(self.matrix[0]-1)
        y = y+y_loc*(self.matrix[1]-1) - (self.lattice=='hexagonal')*(x/2)

        if force:
            if self.lattice == 'cartesian':
                x = max(0,min(int(x),self.matrix[0]))
                y = max(0,min(int(y),self.matrix[1]))
            elif self.lattice == 'hexagonal':
                x = max(0,min(int(x),self.matrix[0]))
                y = max(-x//2,min(int(y),[self.matrix[1],self.matrix[-1]][x%2]-x//2))

        return x,y

    def angle_simplified(angle):
        # returns angle in radians between -180 and 180 degrees
        in_circle = angle%(2*math.pi)
        angle_simple = in_circle if in_circle < math.pi else in_circle-2*math.pi
        return angle_simple

    def angle_hex(angle):
        # finds the trident an angle resides and returns it as phi for sin and cos
        ratio = 3/4
        cutoff = 2*math.pi/3
        theta = CoordinateSystem.angle_simplified(angle)
        if (theta >= 0) & (theta <= cutoff):
            trident = 1
            phi = ratio*theta
        if (theta < 0) & (theta >= -cutoff):
            trident = 3
            phi = ratio*(theta+cutoff)
        else:
            trident = 2
            phi = ratio*(theta-cutoff)

        return phi,trident

    def angle_difference(angle1,angle2):
        # returns minimum difference between angles CW vs CCW
        angle1 = CoordinateSystem.angle_simplified(angle1)
        angle2 = CoordinateSystem.angle_simplified(angle2
                                                   )
        angle1 = angle1 + 2*math.pi if angle1 < 0 else angle1
        angle2 = angle2 + 2*math.pi if angle2 < 0 else angle1
        diff = min(abs(angle1 - angle2),abs(angle2 - angle1))
        diff = min(diff,2*math.pi - diff)
        return diff

    def _is_half(self,position_x):
        # check if position is at half point
        half = round(position_x%1,1)==0.5
        return half

    def neighbors(self,position,half_height=False,half_width=False):
        # list of neighboring cells
        if half_height & half_width:
            half = self._is_half(position[0]) & self._is_half(position[1])
        elif half_height:
            half = self._is_half(position[0])
        elif half_width:
            half = self._is_half(position[1])
        else:
            half = False

        if (self.lattice == 'cartesian') & half:
            directions = [(x/2,y/2) for x,y in self.directions[len(self.directions)//2:]] # half cell positions are diagonals only
        else:
            directions = self.directions
        neighbor_cells = [(round(position[0]+direction[0]),round(position[1]+direction[1])) for direction in directions]

        if self.matrix:
            if self.lattice == 'cartesian':
                neighbor_cells = [neighbor for neighbor in neighbor_cells if \
                    (neighbor[0] >= 0) & (neighbor[0] < self.matrix[0]) & \
                    (neighbor[1] >= 0) & (neighbor[1] < self.matrix[1])]
            elif self.lattice == 'hexagonal':
                neighbor_cells = [neighbor for neighbor in neighbor_cells if \
                    (neighbor[0] >= 0) & (neighbor[0] < self.matrix[0]) & \
                    (neighbor[1] >= -(neighbor[0]//2)) & (neighbor[1] < self.matrix[1] - (neighbor[0]//2))]

        return neighbor_cells

    def _is_even(self,matrix):
        # determin if matrix is even
        # an even matrix has an even width at the center of the height
        # if height is an even number, width is at the even if height is 2 * even, else odd
        # if height is an odd number, width is at the evens
        if matrix[0]%2:
            w = matrix[1]
        elif (matrix[0]/2)%2:
            w = matrix[-1]
        else:
            w = matrix[1]
        even = (w%2 == 0)
        return even

    def get_positions(self,rings=None,width=None):
        # return all positions in matrix or positions in a ring
        positions = None
        
        if width:
            rings = width//2

        if rings is not None:
            if self.matrix:
                # check if even and create regular coordinate system
                CS = CoordinateSystem(lattice=self.lattice,even=self._is_even(self.matrix))
                cs_positions = CS.get_positions(rings=rings,width=width)
                positions = [self.in_matrix(position,force=True) for position in cs_positions]
                
            else:
                range_n = range(self.even,self._ring_start(rings+1)+1)
                positions = [self.n_to_position(n) for n in range_n]

        elif self.matrix:
            if self.lattice == 'cartesian':
                positions = [(x,y) for x in range(self.matrix[0]) for y in range(self.matrix[1])]
            elif self.lattice == 'hexagonal':
                positions = [(2*x,y-x) for x in range(math.ceil(self.matrix[0]/2)) for y in range(self.matrix[1])] \
                          + [(2*x+1,y-x) for x in range(math.floor(self.matrix[0]/2)) for y in range(self.matrix[-1])]               
        
        return positions

    def n_total(self):
        # return number of cells in a matrix
        if self.matrix:
            if self.even:
                N = self.matrix[0] * 1/2 * (self.matrix[1] + self.matrix[-1])
            else:
                N = math.ceil(self.matrix[0]/2) * self.matrix[1] + math.floor(self.matrix[0]/2) * self.matrix[-1]
        else:
            N = None
        return N

    def ring_size(self,ring=0,width=0):
        # how many are containted in a ring
        if width:
            ring = width//2
        size = self._ring_start(ring+1)
        return size

    def path_finder(self,position1,position2=None,to_edge=False,normalize=False):
        # return shortest path between cells
        if position2:
            if self.lattice == 'cartesian':
                routes = [abs(position1[0]-position2[0]),
                          abs(position1[1]-position2[1])]
            elif self.lattice == 'hexagonal':
                routes = sorted([abs(position1[0]-position2[0]),
                                 abs(position1[1]-position2[1]),
                                 abs(-(position1[0]+position1[1])+(position2[0]+position2[1]))])
            path = routes[0] + routes[1]
        elif to_edge:
            if self.lattice == 'cartesian':
                edge_N = self.matrix[0],position1[0]
                edge_S = 0,position1[0]
                edge_W = position1[0],0
                edge_E = position1[0],self.matrix[1]
            elif self.lattice == 'hexagonal':
                offset = position1[0]//2
                edge_N = self.matrix[0],position1[1] + offset - self.matrix[0]//2
                edge_S = 0,position1[1] + offset
                edge_W = position1[0],0 - offset
                edge_E = position1[0],[self.matrix[1],self.matrix[-1]][position1[0]%2] - offset
            if normalize:
                normal_NS = self.matrix[0]/2
                normal_WE = (self.matrix[1]+self.matrix[-1])/4
                normal = [normal_NS,normal_NS,normal_WE,normal_WE]
            else:
                normal = [1,1,1,1]
            edges = zip([edge_N,edge_S,edge_W,edge_E],normal)
            path = min(self.path_finder(position1,edge[0])/edge[1] for edge in edges)
        return path

    def flip(self,position):
        # flip a position from HW to WH
        return

    def convert_height(self,height,inverse=False):
        # convert lattice matrix height
        if self.lattice == 'hexagonal':
            if inverse:
                height = math.floor(height*4/3)
            else:
                height_even = 1-height%2
                height = math.ceil(height/2) + math.floor(height/2)/2 + 1/4*height_even
        return height

    def convert_width(self,width,inverse=False,even=False):
        # convert lattice matrix width
        if self.lattice == 'hexagonal':
            hex,extra = self.scaling
            ex = extra if even else 0
            if inverse:
                width = (width-ex)/hex
            else:
                width = width*hex+ex
        return width

    def convert_aspect(self,aspect):
        # give an aspect ratio relative to matrix
        if self.lattice == 'hexagonal':
            aspect = self.convert_height(aspect[0],inverse=True), self.convert_width(aspect[1],inverse=True) # even??
        return aspect

    def convert_dimensions(self,height:int,width:int,width2:int=None):
        # converts lattice matrix dimensions
        if self.lattice == 'hexagonal':
            even =(height>1) & ((width==width2) | (width2 is None))
            if width2:
                width = max([width,width2])
            height = self.convert_height(height)
            width = self.convert_width(width,even=even)
        return height,width