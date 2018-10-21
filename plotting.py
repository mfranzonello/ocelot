### PLOTTING OBJECTS ###
import math

class CoordinateSystem:
    def __init__(self,lattice='cartesian',matrix=False):
        # cartesian: (x,y)
        # hexagonal: (x,y,z=-(x+y))
        lattices = {'cartesian': {'sides':4,
                                  'coordinates':2,
                                  'adjustments':[(-1,0,1,0),
                                                 (0,-1,0,1)],
                                  'directions':[(1,0), # add x
                                                (0,1), # add y
                                                (-1,0), # subtract x
                                                (0,-1)]}, # subtract y
                    'hexagonal': {'sides':6,
                                  'coordinates':3,
                                  'adjustments':[(-1,-1,0,1,1,0),
                                                 (1,0,-1,-1,0,1)],
                                  'directions':[(1,0), # add x
                                                (0,1), # add y
                                                (1,-1), # add z
                                                (-1,0), # subtract x
                                                (0,-1), # subtract y
                                                (-1,1)]}} # subtract z
        
        self.lattice = lattice
        self.matrix = matrix

        self.sides = lattices[lattice]['sides']
        self.coordinates = lattices[lattice]['coordinates']
        self.adjustments = lattices[lattice]['adjustments']
        self.directions = lattices[lattice]['directions']

    def distance(self,position1,position2):
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
        adj = 1 if self.sides == 4 else 0
        n_in = ring*(1+adj)
        return n_in

    def _ring_start(self,ring):
        # starting n for a ring
        adj = 1 if self.sides == 4 else 0 # square systems sides multiple faster
        start = sum([self._n_in_side(r)*self.sides for r in range(ring)]) # + last = -1 if self.sides == 3 else 0
        return start

    def _position_to_ring(self,position):
        # given (x,y) return ring
        ring = math.ceil(self.distance((0,0),position))
        return ring

    def _n_to_ring(self,n):
        # given vertex return ring
        ring = 0
        last = 0
        adj = 1 if self.sides == 4 else 0 # square systems start with a larger first ring

        while n > last:
            ring += 1
            last += (ring+adj)*self.sides

        return ring

    def n_to_position(self,n):
        # given vertex return (x,y)
        if self.matrix:
            if self.lattice == 'cartesian':
                position = (n//self.matrix[1],n%matrix[1])
            elif self.lattice == 'hexagonal':
                position = (n//self.matrix[1],n%matrix[1]-(n//self.matrix[1])//2)

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
                x = x_side_adj + x_in_side_adj + ring
                y = y_side_adj + y_in_side_adj

                position = (x,y)

        return position

    def position_to_n(self,position):
        # given (x,y) return vertex
        if self.matrix:
            if self.lattice == 'cartesian':
                position[0] * self.matrix[1] + position[1]
            elif self.lattice == 'hexagonal':
                position[0] * self.matrix[1] + position[1] ## ADJUST

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
        # convert (x,y) to R,theta with theta in radians between 0 and 260 degrees
        R = self.distance(position,(0,0))
        cart_xy = self.to_rectangular(position)
        theta = math.atan2(cart_xy[1],cart_xy[0])
        if theta < 0:
            theta = 2*math.pi + theta
        return R,theta

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

    def neighbors(self,position):
        # list of neighboring cells
        neighbor_cells = [(position[0]+direction[0],position[1]+direction[1]) for direction in self.directions]

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
