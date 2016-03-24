import math

# Point in 2D
# Implements operations on points, such as +,-,*,/ etc
# as well as distance, dot product and determinant/cross product
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, p):
        return Point(self.x + p.x, self.y + p.y)

    def __sub__(self, p):
        return self + (-p)

    def __mul__(self, t):
        return Point(self.x * t, self.y * t)

    def __div__(self, t):
        return Point(self.x / float(t), self.y / float(t))

    def __pos__(self):
        return self.clone()

    def __neg__(self):
        return self * (-1)

    def __cmp__(self, p):
        return cmp(self.to_tuple(), p.to_tuple())

    def __str__(self):
        #return "(%s, %s)" % (self.x, self.y)
        return self.__repr__()

    def __repr__(self):
        return "Point(%s, %s)" % (self.x, self.y)

    def to_tuple(self):
        return (self.x, self.y)

    def clone(self):
        return Point(self.x, self.y)

    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def move(self, dx, dy):
        return self + Point(dx, dy)

    def normalize(self):
        return self / self.length()

    def distance_to(self, p):
        return (self - p).length()

    def signed_angle_between(self, p):
        # Based on http://stackoverflow.com/a/2150475
        a = math.atan2(self.det(p), self.dot(p))
        return a if a >= 0 else a + 2*math.pi

    def dot(self, p):
        return self.x * p.x + self.y * p.y

    def det(self, p):
        return self.x * p.y - self.y * p.x

    def flip(self):
        return Point(-self.y, self.x)

    # Define constants for better readability
    LEFT_TURN, RIGHT_TURN, COLINEAR = (1, -1, 0)

    # Returns 1, -1, 0 if p,q,r forms a left turn, a right turn or are colinear.
    @staticmethod
    def turn(p, q, r):
        return cmp(p.det(q) + r.det(p) + q.det(r), 0)

class Box:
    # Takes topleft and bottomright point of box
    def __init__(self, topleft, botright):
        self.topleft = topleft
        self.botright = botright

    def to_tuple(self):
        return (self.topleft.x, self.topleft.y, self.botright.x, self.botright.y)
    
    def width(self):
        return self.botright.x - self.topleft.x

    def height(self):
        return self.botright.y - self.topleft.y

    def dim(self):
        return self.width(), self.height()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "Box(%s, %s)" % (self.topleft, self.botright)

    def __add__(self, other):
        if isinstance(other, Point):
            return Box(self.topleft + other, self.botright + other)
        elif isinstance(other, Box):
            return Box(self.topleft + other.topleft, self.botright + other.botright)

    def __sub__(self, other):
        return self + (-other)

    def __mul__(self, t):
        return Box(self.topleft * t, self.botright * t)

    def __div__(self, t):
        return Box(self.topleft / t, self.botright / t)

    def __pos__(self):
        return self.clone()

    def __neg__(self):
        return self * (-1)

    def clone(self):
        return Box(self.topleft.clone(), self.botright.clone())




# A snapshot of the current scene
# It has a ball point, a target point and a timestamp since we started the current sampling
class Snapshot:
    def __init__(self, ball_pos, target_pos, timestamp):
        self.ball_pos = ball_pos
        self.target_pos = target_pos
        self.timestamp = timestamp

    def __str__(self):
        return "%s, %s, %s" % (self.ball_pos, self.target_pos, self.timestamp)

    def __repr__(self):
        return str(self)
