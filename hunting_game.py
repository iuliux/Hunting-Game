import cherrypy
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
    N = 10
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
            table[i.x][i.y] = i
        for i in self.prey:
            table[i.x][i.y] = i

        return ''.join(['<tr>'+str(
                    ''.join([str(cell) for cell in row])
                )+'</tr>\n' for row in table])

    def run(self):
        while True:
            for i in self.prey:
                direction = int(random.uniform(0, 4))
                # i.move(direction)

            time.sleep(1)


world = World()


class AjaxApp(object):
    @cherrypy.expose
    def index(self):
        return open(os.path.join(MEDIA_DIR, u'index.html'))

    @cherrypy.expose
    def submit(self):
        table = world.compile_representation()
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(dict(repr=table))


cherrypy.tree.mount(AjaxApp(), '/', config=config)
cherrypy.engine.start()
