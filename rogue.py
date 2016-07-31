import libtcodpy as libtcod

#size of window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

#max FPS
LIMIT_FPS = 20

#size of map
MAP_WIDTH = 80
MAP_HEIGHT = 45

#room constants
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_MONSTERS = 3

#Field of view constants
FOV_ALGO = 0
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10


#basic map colors
color_dark_wall = libtcod.Color(0,0,100)
color_dark_ground = libtcod.Color(50,50,150)
color_light_wall = libtcod.Color(130,110,50)
color_light_ground = libtcod.Color(200,180,50)


class Tile:
	#a tile of the map and its properties
	def __init__(self, blocked, block_sight = None):
		self.blocked = blocked
		self.explored = False
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
	
	def center(self):
		center_x = ((self.x1 + self.x2) / 2)
		center_y = ((self.y1 + self.y2) / 2)
		return(center_x, center_y)


	def intersect(self, other):
		#returns true if this overlaps other
		return (self.x1 <= other.x2 and self.y1 <= other.y2
				and self.x2 >= other.x1 and self.y2 >= other.y1)

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
		#if the object is in FOV
		if libtcod.map_is_in_fov(fov_map, self.x, self.y):
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

	#create random map by basic method
	rooms = []
	num_rooms = 0

	for r in range(MAX_ROOMS):
		#randome width and height
		w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
		y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

		#make a rect of each room
		new_room = Rect(x,y,w,h)

		#run through the previous room to make sure there is no intersecting
		failed = False
		for other_room in rooms:
			if new_room.intersect(other_room):
				failed = True
				break		

		if not failed:
			#there are no bad intersections with other rooms
			create_room(new_room)

			(new_x, new_y) = new_room.center()

			if num_rooms == 0:
				#the player starts in the first room!
				player.x = new_x
				player.y = new_y
			else:
				# if it is not first, connect to previous with a tunnel

				(prev_x, prev_y) = rooms[num_rooms-1].center()


				if libtcod.random_get_int(0, 0, 1) == 1:
					print (prev_x, new_x, prev_y)
					create_h_tunnel(prev_x, new_x, prev_y)
					create_v_tunnel(prev_y, new_y, new_x)
				else:
					create_h_tunnel(prev_x, new_x, new_y)
					create_v_tunnel(prev_y, new_y, prev_x)

			#once a valid room is drawn and connected, store it in rooms and move on to the next
			place_objects(new_room)
			rooms.append(new_room)
			num_rooms += 1

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
	for y in range(min(y1,y2),max(y1,y2)+1):
		map[x][y].blocked = False
		map[x][y].block_sight = False

def render_all():
	global color_light_wall
	global color_light_ground
	global fov_map
	global fob_recompute

	#recompute FOV if needed (the player moved or something)
	fov_recompute = False
	libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
	#set background colors for all tiles
	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			visible = libtcod.map_is_in_fov(fov_map, x, y)
			wall = map[x][y].block_sight
			if not visible:
				if map[x][y].explored:
					if wall:
						libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET )
					else:
						libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET )
			else:
				if wall:
					libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET )
				else:
					libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET )
				map[x][y].explored = True
	
	#draw all objects in the list
	for object in objects:
		object.draw()
	
	#blit the contents
	libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)

def place_objects(room):
	#choose random number of monsters
	num_monsters = libtcod.random_get_int(0,0,MAX_ROOM_MONSTERS)

	for i in range(num_monsters):
		#choose random spot for this monster
		x = libtcod.random_get_int(0, room.x1, room.x2)
		y = libtcod.random_get_int(0, room.y1, room.y2)

		if libtcod.random_get_int(0,0,100) < 80:
			#80% chance of orc
			monster = Object(x,y,'o', libtcod.desaturated_green)
		else:
			#create a troll
			monster = Object(x,y,'T', libtcod.darker_green)

		objects.append(monster)

def handle_keys():
	"""Handle_keys reads keypresses from the player while in console mode"""

	#no longer required with creation of player object
#	global playerx, playery
	global fov_map
	global fov_recompute
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
		fov_recompute = True
	elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
		player.move(0,1)
		fov_recompute = True
	elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
		player.move(-1,0)
		fov_recompute = True
	elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
		player.move(1,0)
		fov_recompute = True

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

fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
for y in range(MAP_HEIGHT):
	for x in range(MAP_WIDTH):
		libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)
fov_recompute = False

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

