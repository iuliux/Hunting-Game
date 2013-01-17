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
        return '<td style="background:#36679C">%d</td>' % self.nr
        # return '%dx%d' % (self.x, self.y)


class Prey(Cell):
    def __repr__(self):
        return '<td style="background:#B50724">%d</td>' % self.nr
        # return '%dx%d' % (self.x, self.y)


class World(object):
    '''Constants'''
    N = 25
    N_HUNT = 12
    N_PREY = 5
    RESPAWN_TIME = 5  # iterations

    def __init__(self):
        super(World, self).__init__()
        self.hunters = []
        self.prey = []
        already_filled = []

        self.iteration_round = 0

        # Used to respawn dead prey
        self.respawn_countdowns = []

        print "Spawn", World.N_HUNT, 'hunters'
        print "Spawn", World.N_PREY, 'prey'

        for i in xrange(World.N_HUNT):
            self.hunters.append(Hunter(i, World.N, already_filled))
            already_filled.append((self.hunters[-1].x, self.hunters[-1].y))

        for i in xrange(World.N_PREY):
            self.prey.append(Prey(i, World.N, already_filled))
            already_filled.append((self.prey[-1].x, self.prey[-1].y))

    def reinit(self):
        self.__init__()

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

    def distance(self, a, b):
        '''Computes Manhattan distance between 2 cells'''
        return abs(a.x - b.x) + abs(a.y - b.y)

    def score_directions(self, h):
        scores = [0, 0, 0, 0]
        # Weak rejection force from other hunters
        for j in self.hunters:
            if h==j:
                continue
            dist = float(self.distance(h, j)) + 1
            # Vertical
            if j.x < h.x:
                scores[2] += 1 / (dist ** 2)
            elif j.x > h.x:
                scores[0] += 1 / (dist ** 2)
            # Horizontal
            if j.y < h.y:
                scores[1] += 1 / (dist ** 2)
            elif j.y > h.y:
                scores[3] += 1 / (dist ** 2)
        # Strong attraction force from prey
        for j in self.prey:
            dist = float(self.distance(h, j)) + 1
            # Vertical
            if j.x < h.x:
                scores[0] += 10 / (dist ** 2)
            elif j.x > h.x:
                scores[2] += 10 / (dist ** 2)
            # Horizontal
            if j.y < h.y:
                scores[3] += 10 / (dist ** 2)
            elif j.y > h.y:
                scores[1] += 10 / (dist ** 2)
        print scores
        return scores

    def respawn_prey(self):
        already_filled = [(k.x, k.y) for k in self.prey+self.hunters]
        new_idx = self.prey[-1].nr + 1
        self.prey.append(Prey(new_idx, World.N, already_filled))

    def __repr__(self):
        return self.compile_representation()

    def __str__(self):
        return self.__repr__()


world = World()


def iterate():
    print "ITERATION:", world.iteration_round
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
        moves = True
        scores = world.score_directions(i)
        direction = scores.index(max(scores))
        new_pos = world.adjacent_cell(i.x, i.y, direction)
        while (not new_pos or not world.empty_cell(new_pos)) and sum(scores) != 0:
            # If the best direction is blocked, just keep current position
            if not world.empty_cell(new_pos):
                moves = False
                break
            # Take the next biggest
            scores[direction] = 0
            direction = scores.index(max(scores))
            new_pos = world.adjacent_cell(i.x, i.y, direction)
        if moves and sum(scores) != 0:
            # Not completly blocked
            i.move(direction)

    # Check if prey dies
    for i in world.prey:
        if world.prey_trapped(i):
            world.prey.remove(i)
            world.respawn_countdowns.append(World.RESPAWN_TIME)

    # Rounds count
    world.iteration_round += 1
    # Handle respawning
    for i in xrange(len(world.respawn_countdowns)):
        world.respawn_countdowns[i] -= 1
        if world.respawn_countdowns[i] <= 0:
            world.respawn_prey()
    world.respawn_countdowns = [a for a in world.respawn_countdowns if a > 0]


class HuntingGameApp(object):
    @cherrypy.expose
    def index(self):
        return open(os.path.join(MEDIA_DIR, u'index.html'))

    @cherrypy.expose
    def update(self):
        table = str(world)
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(dict(repr=table))

    @cherrypy.expose
    def set(self, hunters, prey):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        if hunters.isdigit() and prey.isdigit():
            if int(hunters) + int(prey) > World.N**2:
                return simplejson.dumps(dict(success='Too many'))
            World.N_HUNT = int(hunters)
            World.N_PREY = int(prey)
            world.reinit()
        else:
            return simplejson.dumps(dict(success='Invalid input'))
        return simplejson.dumps(dict(success='Done'))


Monitor(cherrypy.engine, iterate, frequency=1).subscribe()

cherrypy.config.update({'server.socket_port': 4040})
cherrypy.tree.mount(HuntingGameApp(), '/', config=config)
cherrypy.engine.start()
