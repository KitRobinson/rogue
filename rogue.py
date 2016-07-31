import libtcodpy as libtcod

#size of window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

#max FPS
LIMIT_FPS = 20

#size of map
MAP_WIDTH = 80
MAP_HEIGHT = 45

#basic map colors
color_dark_wall = libtcod.Color(0,0,100)
color_dark_ground = libtcod.Color(50,50,150)



class Tile:
	#a tile of the map and its properties
	def __init__(self, blocked, block_sight = None):
		self.blocked = blocked

		#by default, fif a tile is blocked, it also blocks sight
		if block_sight is None: block_sight = blocked
		self.block_sight = block_sight

class Rect:
	#a rectance on the map, used to characterize a room.
	def __init__(self, x, y, w, h):
		self.x1 = x
		self.y1 = y
		self.x2 = x + w
		self.y2 = y + h

class Object:
	#this si a generic object
	#it is always represented by a character on the screen
	def __init__(self, x, y, char, color):
		self.x = x
		self.y = y
		self.char = char
		self.color = color

	def move(self, dx, dy):
		#move by the given amount
		if not map[self.x + dx][self.y + dy].blocked:
			self.x += dx
			self.y += dy

	def draw(self):
		#set the color and draw the character
		libtcod.console_set_default_foreground(con, self.color)
		libtcod.console_put_char(con, self.x, self.y, self.char , libtcod.BKGND_NONE)

	def clear(self):
		#erase the character that represents this object
		libtcod.console_set_default_foreground(con, self.color)
		libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE )

def make_map():
	global map

	#fill map with unblocked tiles
	map = [[ Tile(True)
		for y in range(MAP_HEIGHT) ]
			for x in range(MAP_WIDTH) ]

	#place 2 pillars for testing
	room1 = Rect(20,15,10,15)
	room2 = Rect(50,15,10,15)
	create_room(room1)
	create_room(room2)
	create_h_tunnel(23,57,22)

def create_room(room):
	global map
	#go through the tiles in the rectangle and make them passable
	for x in range(room.x1 +1, room.x2):
		for y in range(room.y1 + 1, room.y2):
			map[x][y].blocked = False
			map[x][y].block_sight = False

def create_h_tunnel(x1, x2, y):
	global map
	#dig a horizontal tunnel from x1 to x2 at height y
	for x in range(min(x1,x2),max(x1,x2)):
		map[x][y].blocked = False
		map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
	global map
	#dig a horizontal tunnel from x1 to x2 at height y
	for y in range(min(y1,y2),max(y1,y2)):
		map[x][y].blocked = False
		map[x][y].block_sight = False

def render_all():
	global color_light_wall
	global color_light_ground

	#set background colors for all tiles
	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			wall = map[x][y].block_sight
			if wall:
				libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET )
			else:
				libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET )
	
	#draw all objects in the list
	for object in objects:
		object.draw()
	
	#blit the contents
	libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)



def handle_keys():
	"""Handle_keys reads keypresses from the player while in console mode"""

	#no longer required with creation of player object
#	global playerx, playery

	#wait for keypress makes us turn based
	key = libtcod.console_wait_for_keypress(True)

	#function keys
	if key.vk == libtcod.KEY_ENTER and key.lalt:
		#alt-enter toggles fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
	elif key.vk == libtcod.KEY_ESCAPE:
		#escape key exits game function
		return True 
	
	#movement keys
	if libtcod.console_is_key_pressed(libtcod.KEY_UP):
		player.move(0,-1)
	elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
		player.move(0,1)
	elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
		player.move(-1,0)
	elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
		player.move(1,0)

########################################################
# INITIALIZATION AND MAIN LOOP
########################################################

libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

#the coords here are the player starting location
player = Object(25, 23, '@', libtcod.white)
npc = Object(SCREEN_WIDTH/2-5, SCREEN_HEIGHT/2, '&', libtcod.red)
objects = [npc, player]

#generate starting map
make_map()

while not libtcod.console_is_window_closed():

	#render the screen
	render_all()

	libtcod.console_flush()

	#erase obj at old loc before they move
	for object in objects:
		object.clear()

		# this bit no longer required with creation of render all
	# libtcod.console_set_default_foreground(con, libtcod.white)
	# libtcod.console_put_char(con, player.x, player.y, '@', libtcod.BKGND_NONE)
	# libtcod.console_flush()

	#handle kepress, exit game if needed

	exit = handle_keys()
	if exit:
		break

