import cherrypy
from cherrypy.process.plugins import Monitor
import os
import random
import simplejson

MEDIA_DIR = os.path.join(os.path.abspath("."), u"media")


config = {'/media':
                {'tools.staticdir.on': True,
                 'tools.staticdir.dir': MEDIA_DIR,
                }
        }


class Cell:
    def __init__(self, nr=0, table_size=0, already_filled=[]):
        self.nr = nr
        self.x = int(random.uniform(0, table_size) - 1)
        self.y = int(random.uniform(0, table_size) - 1)
        while (self.x, self.y) in already_filled:
            self.x = int(random.uniform(0, table_size))
            self.y = int(random.uniform(0, table_size))

    def move(self, direction):
        ''''Direction direction is represented as int, as follows:
            0 -> Up
            1 -> Right
            2 -> Down
            3 -> Left
        '''
        # Up
        if direction == 0:
            self.x -= 1
        # Right
        elif direction == 1:
            self.y += 1
        # Down
        elif direction == 2:
            self.x += 1
        # Left
        elif direction == 3:
            self.y -= 1

    def __repr__(self):
        return '<td></td>'


class Hunter(Cell):
    def __repr__(self):
        return '<td style="background:#0005ff">%d</td>' % self.nr
        # return '%dx%d' % (self.x, self.y)


class Prey(Cell):
    def __repr__(self):
        return '<td style="background:#ff0500">%d</td>' % self.nr
        # return '%dx%d' % (self.x, self.y)


class World(object):
    '''Constants'''
    N = 14
    N_HUNT = 4
    N_PREY = 2

    def __init__(self):
        super(World, self).__init__()
        self.hunters = []
        self.prey = []
        already_filled = []

        for i in xrange(World.N_HUNT):
            self.hunters.append(Hunter(i, World.N, already_filled))
            already_filled.append((self.hunters[-1].x, self.hunters[-1].y))

        for i in xrange(World.N_PREY):
            self.prey.append(Prey(i, World.N, already_filled))
            already_filled.append((self.prey[-1].x, self.prey[-1].y))

    def compile_representation(self):
        '''Produces a representation of the world as HTML table'''
        table = [[Cell() for k in xrange(World.N)] for k in xrange(World.N)]

        for i in self.hunters:
            table[i.x][i.y] = i
        for i in self.prey:
            table[i.x][i.y] = i

        return ''.join(['<tr>'+str(
                    ''.join([str(cell) for cell in row])
                )+'</tr>\n' for row in table])

    def adjacent_cell(self, x, y, direction):
        '''Returns the adjacent cell from position `(x, y)` in the direction
           `direction` if this cell is empty and withhin the map, `None` else.
        '''
        # Up
        if direction == 0:
            new_x = x - 1
            if new_x < 0:
                return None
            else:
                return (new_x, y)
        # Right
        elif direction == 1:
            new_y = y + 1
            if new_y >= World.N:
                return None
            else:
                return (x, new_y)
        # Down
        elif direction == 2:
            new_x = x + 1
            if new_x >= World.N:
                return None
            else:
                return (new_x, y)
        # Left
        elif direction == 3:
            new_y = y - 1
            if new_y < 0:
                return None
            else:
                return (x, new_y)

    def empty_cell(self, pos):
        '''Checks if the cell is empty'''
        for i in self.hunters:
            if (i.x, i.y) == pos:
                return False
        for i in self.prey:
            if (i.x, i.y) == pos:
                return False
        return True

    def prey_trapped(self, p):
        '''Checks if the prey p is trapped between hunters (or walls)'''
        neighs = [self.adjacent_cell(p.x, p.y, 0),
                    self.adjacent_cell(p.x, p.y, 1),
                    self.adjacent_cell(p.x, p.y, 2),
                    self.adjacent_cell(p.x, p.y, 3)]
        neighs = [x for x in neighs if x]

        for i in self.hunters:
            if (i.x, i.y) in neighs:
                neighs.remove((i.x, i.y))

        if not neighs:
            return True
        return False

    def score_directions(self, h):
        scores = [0, 0, 0, 0]
        # Weak rejection force from other hunters
        for j in self.hunters:
            if h==j:
                continue
            # Vertical
            if j.x < h.x:
                scores[2] += 1
            elif j.x > h.x:
                scores[0] += 1
            # Horizontal
            if j.y < h.y:
                scores[1] += 1
            elif j.y > h.y:
                scores[3] += 1
        # Strong attraction force from prey
        for j in self.prey:
            # Vertical
            if j.x < h.x:
                scores[0] += 3
            elif j.x > h.x:
                scores[2] += 3
            # Horizontal
            if j.y < h.y:
                scores[3] += 3
            elif j.y > h.y:
                scores[1] += 3
        return scores

    def __repr__(self):
        return self.compile_representation()

    def __str__(self):
        return self.__repr__()


world = World()


def iterate():
    print "ITERATES"
    # Prey movement
    for i in world.prey:
        # print '   ', i
        direction = int(random.uniform(0, 4))
        # print '    DIR:', direction
        new_pos = world.adjacent_cell(i.x, i.y, direction)
        # print '    newPOS:', new_pos
        while not new_pos or not world.empty_cell(new_pos):
            direction = int(random.uniform(0, 4))
            new_pos = world.adjacent_cell(i.x, i.y, direction)
        i.move(direction)

    # Hunters movement
    for i in world.hunters:
        scores = world.score_directions(i)
        direction = scores.index(max(scores))
        new_pos = world.adjacent_cell(i.x, i.y, direction)
        while (not new_pos or not world.empty_cell(new_pos)) and sum(scores) != 0:
            # Take the next biggest
            scores[direction] = 0
            direction = scores.index(max(scores))
            new_pos = world.adjacent_cell(i.x, i.y, direction)
        if sum(scores) != 0:
            # Not blocked
            i.move(direction)

    # Check if prey dies
    for i in world.prey:
        if world.prey_trapped(i):
            world.prey.remove(i)


class HuntingGameApp(object):
    @cherrypy.expose
    def index(self):
        return open(os.path.join(MEDIA_DIR, u'index.html'))

    @cherrypy.expose
    def submit(self):
        table = str(world)
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(dict(repr=table))


Monitor(cherrypy.engine, iterate, frequency=1).subscribe()

cherrypy.config.update({'server.socket_port': 4040})
cherrypy.tree.mount(HuntingGameApp(), '/', config=config)
cherrypy.engine.start()
