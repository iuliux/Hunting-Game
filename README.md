Hunting Game
============

Intro
-----
Simulation of a grid enviroment where some hunters try to surround the prey and kill it.
While the prey moves randomly on the map (only up-right-down-left one cell moves are allowed), the hunters move by a specific heuristic:
- strongly attracted by prey near them
- slightly rejected by other hunters near them

The forces (attraction/rejection) are fading quadratically with (Manhattan) distance.

Demo
----
Hosted on Heroku: http://hunting-game.herokuapp.com/

Tools
-----
- [CherryPy](http://www.cherrypy.org)
- JQuery
- [SimpleJSON](http://code.google.com/p/simplejson)
