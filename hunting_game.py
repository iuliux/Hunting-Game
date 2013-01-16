import cherrypy
from cherrypy.process.plugins import Monitor

import os
import random
import simplejson
import time
from threading import Thread

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


class World(Thread):
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

        print 'Hunters', self.hunters
        print 'Prey', self.prey
        print self.compile_representation()

    def compile_representation(self):
        table = [[Cell() for k in xrange(World.N)] for k in xrange(World.N)]

        for i in self.hunters:
            # print '>>>>>>>>>>', i.x, '-', i.y, '<<<<<<<<<<<<<'
            table[i.x][i.y] = i
        for i in self.prey:
            # print '>>>>>>>>>>', i.x, '-', i.y, '<<<<<<<<<<<<<'
            table[i.x][i.y] = i

        return ''.join(['<tr>'+str(
                    ''.join([str(cell) for cell in row])
                )+'</tr>\n' for row in table])

    def adjacent_cell(self, x, y, direction):
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
        for i in self.hunters:
            if (i.x, i.y) == pos:
                return False
        for i in self.prey:
            if (i.x, i.y) == pos:
                return False
        return True


world = World()


def iterate():
    print "ENTERS"
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

    # print "HULALA"
        # time.sleep(1)


class HuntingGameApp(object):
    @cherrypy.expose
    def index(self):
        return open(os.path.join(MEDIA_DIR, u'index.html'))

    @cherrypy.expose
    def submit(self):
        table = world.compile_representation()
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(dict(repr=table))


Monitor(cherrypy.engine, iterate, frequency=1).subscribe()

cherrypy.config.update({'server.socket_port': 4040})
cherrypy.tree.mount(HuntingGameApp(), '/', config=config)
cherrypy.engine.start()
