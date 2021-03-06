import libtcodpy as libtcod
import math
import textwrap
#size of window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

#max FPS
LIMIT_FPS = 20

#size of map
MAP_WIDTH = 80
MAP_HEIGHT = 43

#room constants
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_MONSTERS = 3 
MAX_ROOM_ITEMS = 2 

#Field of view constants
FOV_ALGO = 0
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

#bar constants
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

#message bar constants
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH -2
MSG_HEIGHT = PANEL_HEIGHT -1
INVENTORY_WIDTH = 50

#spell constants
LIGHTNING_DAMAGE = 20
LIGHTNING_RANGE = 5
HEAL_AMOUNT = 4
CONFUSE_NUM_TURNS = 10
CONFUSE_RANGE = 8
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 12
#more constants
INV_CAP = 26

#basic map colors
color_dark_wall = libtcod.Color(0,0,100)
color_dark_ground = libtcod.Color(50,50,150)
color_light_wall = libtcod.Color(130,110,50)
color_light_ground = libtcod.Color(200,180,50)

#define starting game state
game_state = 'playing'
player_action = None

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

class Fighter:
	#combat related properties and methods (monster, player, npc)
	def __init__(self, hp, defense, power, death_function=None):
		self.max_hp = hp
		self.hp = hp
		self.defense = defense
		self.power = power
		self.death_function = death_function

	def take_damage(self, damage):
		#apply damage if possible
		if damage > 0:
			self.hp -= damage
		if self.hp <= 0:
			function = self.death_function
			if function is not None:
				function(self.owner)

	def attack(self, target):
		#a very simple formula for attack damage
		damage = self.power - target.fighter.defense

		if damage > 0:
			#make the target take some damage!
			message((self.owner.name.capitalize() + ' attacks ' + target.name.capitalize() +' for ' + str(damage) + ' damage!'), libtcod.white)
			target.fighter.take_damage(damage)
		else:
			message((self.owner.name.capitalize() + ' attacks ' + target.name.capitalize() + ' but has no effect!'), libtcod.white)

	def heal(self, amount):
		#heal by the given amount, without going over the max
		self.hp += amount
		if self.hp > self.max_hp:
			self.hp = self.max_hp

class BasicMonster:
	#AI for most basic monstere turn
	def take_turn(self):
		#a basic monster takes its turn.  if you can see it, it can see you
		monster = self.owner
		if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):

			#move towards the player if far away
			if monster.distance_to(player) >= 2:
				monster.move_towards(player.x, player.y)

			#attack if adjacent
			elif player.fighter.hp > 0:
				monster.fighter.attack(player)

class ConfusedMonster:

	def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
		self.old_ai = old_ai
		self.num_turns = num_turns
	#AI for confused monster
	def take_turn(self):
		if self.num_turns > 0:
			rand_x = libtcod.random_get_int(0, -1, 1)
			rand_y = libtcod.random_get_int(0, -1, 1)
			for object in objects:
				if object.x == self.owner.x + rand_x and object.y == self.owner.y + rand_y and object.fighter:
					self.owner.fighter.attack(object)
					self.num_turns -= 1
					break
				else:
					self.owner.move(rand_x, rand_y)
					self.num_turns -= 1
					break
		else:
			self.owner.ai = self.old_ai
			message('The ' + self.owner.name + ' is no longer confused', libtcod.red)
		#a confused monster moves randomly, and attacks randomly

class Item:

	def __init__(self, use_function=None):
		self.use_function=use_function

	#an item that can be picked up and used
	def pick_up(self):
	#add to players inventory and remove from map
		if len(inventory) >= INV_CAP:
			message('your inventory is full!  did not pick up' + self.owner.name + '.')			
		else:
			inventory.append(self.owner)
			objects.remove(self.owner)
			message('you picked up a ' + self.owner.name + "!", libtcod.green)

	def use(self):
		#just call the use function if it is defined
		if self.use_function is None:
			message('The ' + self.owner.name + ' cannot be used.')
		else:
			if self.use_function() != 'cancelled':
				inventory.remove(self.owner) # destroy after use, unless it was cancelled for some reason

	def drop(self, x, y):
		self.owner.x = x
		self.owner.y = y
		objects.append(self.owner)
		inventory.remove(self.owner)
		self.owner.send_to_back()


class Object:
	#this si a generic object
	#it is always represented by a character on the screen
	def __init__(self, x, y, char, name, color, blocks=False, fighter=None, ai=None, item=None):
		self.x = x
		self.y = y
		self.char = char
		self.name = name
		self.color = color
		self.blocks = blocks
		self.fighter = fighter
		if self.fighter:
			self.fighter.owner = self
		self.ai = ai
		if self.ai:
			self.ai.owner = self
		self.item = item
		if self.item:
			self.item.owner = self

	def send_to_back(self):
		global objects
		objects.remove(self)
		objects.insert(0, self)


	def move(self, dx, dy):
		#move by the given amount
		if not is_blocked(self.x + dx, self.y + dy):
			self.x += dx
			self.y += dy

	def move_towards(self, target_x, target_y):
		#vector from this object toe the target, and distance
		dx = target_x - self.x
		dy = target_y - self.y
		distance = math.sqrt(dx ** 2 + dy ** 2)

		#normalse it to lenght 1 (preserving direction), then round it and 
		#conver to integer so the movement is restircted to the map grid
		dx = int(round(dx/distance))
		dy = int(round(dy/distance))
		self.move(dx, dy)


	def distance(self, x, y):
		return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

	def distance_to(self, other):
		#return the distance to another object
		dx = other.x - self.x
		dy = other.y - self.y
		return math.sqrt(dx ** 2 + dy ** 2)

	def draw(self):
		#if the object is in FOV
		if libtcod.map_is_in_fov(fov_map, self.x, self.y):
			#set the color and draw the character
			libtcod.console_set_default_foreground(con, self.color)
			libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

	def clear(self):
		#erase the character that represents this object
		libtcod.console_set_default_foreground(con, self.color)
		libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE )


###############################################################
#				Non-class methods
###############################################################


def is_blocked(x,y):
	#first test the map tile
	if map[x][y].blocked:
		return True
	else:
		#now check for blocking objects
		for object in objects:
			if object.x == x and object.y == y and object.blocks:
				return True

	return False

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
					create_h_tunnel(prev_x, new_x, prev_y)
					create_v_tunnel(prev_y, new_y, new_x)
				else:
					create_h_tunnel(prev_x, new_x, new_y)
					create_v_tunnel(prev_y, new_y, prev_x)

			#once a valid room is drawn and connected, store it in rooms and move on to the next
			place_objects(new_room)
			rooms.append(new_room)
			num_rooms += 1

def closest_monster(max_range):
	closest_enemy = None
	closest_dist = max_range + 1

	for object in objects:
		if object.fighter and not object == player and libtcod.map_is_in_fov(fov_map, object.x, object.y):
			dist = player.distance_to(object)
			if dist < closest_dist:
				closest_enemy = object
				closest_dist = dist
	return closest_enemy

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

def player_move_or_attack(dx, dy):
	global fov_recompute
	
	#coords the player is trying to go to
	x = player.x + dx
	y = player.y + dy

	#try to find an attackable object there
	target = None
	for object in objects:
		if object.x == x and object.y == y and object.fighter:
			target = object
			break

	#attack if target found
	if target is not None:
		player.fighter.attack(target)
	else:	
		player.move(dx,dy)
		fov_recompute = True

def render_all():
	global color_light_wall
	global color_light_ground
	global fov_map
	global fob_recompute
	#show the player's stats
	libtcod.console_set_default_foreground(con, libtcod.white)
	libtcod.console_print_ex(con, 1, SCREEN_HEIGHT-1, libtcod.BKGND_NONE, libtcod.LEFT, 'HP: ' +  str(player.fighter.hp) + '/' + str(player.fighter.max_hp))

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
	player.draw()
	#display status bar
	libtcod.console_set_default_background(panel, libtcod.black)
	libtcod.console_clear(panel)
	# print the messages to the message panel
	y = 1 
	for (line, color) in game_msgs:
		libtcod.console_set_default_foreground(panel, color)
		libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
		y += 1

	render_bar(1,1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp, libtcod.light_red, libtcod.darker_red)
	#blit the contents
	libtcod.console_blit(panel,0,0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)
	libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)

def cast_fireball():
	message('left-click a target tile, or right click to cancel', libtcod.light_cyan)
	(x,y) = target_tile()
	if x is None: return 'cancelled'
	message('the fireball explodes, burning everything within' + str(FIREBALL_RADIUS) + 'tiles!')

	for obj in objects: #damage everything with a fighter
		if obj.distance(x,y) <= FIREBALL_RADIUS and obj.fighter:
			message('The ' + obj.name + ' gets burned for ' +str(FIREBALL_DAMAGE) + ' hit points')
			obj.fighter.take_damage(FIREBALL_DAMAGE)

def cast_heal():
	if player.fighter.hp < player.fighter.max_hp:
		message('Your wounds start to feel better!', libtcod.light_violet)
		player.fighter.heal(HEAL_AMOUNT)
	else:
		message('You are already at full heath', libtcod.light_violet)
		return 'cancelled'

def cast_lightning():
	#find closest enemy inside max range and damage it
	monster = closest_monster(LIGHTNING_RANGE)
	if monster is None: #no enemy found within max range
		message('No emeny is close enough to strike', libtcod.red)
		return 'cancelled'
	message('A lightning bolt strikes the ' + monster.name + 'with a thunderous boom!  the damae is ' + str(LIGHTNING_DAMAGE) + ' hit points.', libtcod.light_blue)
	monster.fighter.take_damage(LIGHTNING_DAMAGE)

def cast_confuse():
	#confuse the closest monster
	message('left click an enemy to cast confuse, or right click to cancel')
	monster = target_monster(CONFUSE_RANGE)
	if monster is None: #no enemy in range
		return 'cancelled'
	else:
		old_ai = monster.ai
		monster.ai = ConfusedMonster(old_ai)
		monster.ai.owner = monster
		message('The eyes of the ' + monster.name + ' look vacant, as he starts to stumble around!', libtcod.light_green)

def place_objects(room):
	#choose random number of monsters
	num_monsters = libtcod.random_get_int(0,0,MAX_ROOM_MONSTERS)

	for i in range(num_monsters):
		#choose random spot for this monster
		x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
		y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
		if not is_blocked(x,y):
			if libtcod.random_get_int(0,0,100) < 80:
				#80% chance of orc
				fighter_component = Fighter(hp=10, defense=0, power=3, death_function=monster_death)
				ai_component = BasicMonster()
				monster = Object(x, y, 'o', 'Orc', libtcod.desaturated_green, blocks=True, fighter=fighter_component, ai=ai_component)
			else:
				#create a troll
				fighter_component = Fighter(hp=16, defense=1, power=4, death_function=monster_death)
				ai_component = BasicMonster()
				monster = Object(x, y,'T', 'Troll', libtcod.darker_green, blocks=True, fighter=fighter_component, ai=ai_component)

			objects.append(monster)
	

	num_items = libtcod.random_get_int(0,0,MAX_ROOM_ITEMS)

	for i in range(num_items):
		x = libtcod.random_get_int(0,room.x1+1, room.x2-1)
		y = libtcod.random_get_int(0,room.y1+1, room.y2-1)

		if not is_blocked(x,y):
			dice = libtcod.random_get_int(0,0,100)
		
			if dice < 60:
				#create a healing potion
				item_component = Item(use_function=cast_heal)
				item = Object(x,y, '!', 'healing potion', libtcod.violet, item=item_component)
				objects.append(item)
				item.send_to_back
			elif dice < 73:	
				#create a confuse scroll
				item_component = Item(use_function=cast_confuse)
				item = Object(x, y, '#', 'scroll of confusion', libtcod.orange, item=item_component)
				objects.append(item)
				item.send_to_back
			elif dice < 86:
				#fireball scroll
				item_component = Item(use_function=cast_fireball)
				item = Object(x, y, '#', 'scroll of fireball', libtcod.dark_red, item=item_component)
				objects.append(item)
				item.send_to_back
			else:
				#create a lightning scroll
				item_component = Item(use_function=cast_lightning)
				item = Object(x, y, '#', 'scroll of lightning bolt', libtcod.light_yellow, item=item_component)
				objects.append(item)
				item.send_to_back

def menu(header, options, width):
	if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options')
	#calculate total height for the header, and one line per option
	header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
	height = len(options) + header_height
	#create off-screen console that represeents menu's window
	window = libtcod.console_new(width, height)
	#print the header, with auto-wrap
	libtcod.console_set_default_foreground(window, libtcod.white)
	libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)
	#print each option
	y = header_height
	letter_index = ord('a')
	for option_text in options:
		text = '(' + chr(letter_index) + ')' + option_text
		libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
		y += 1
		letter_index += 1
	#blit the contents of window to the root console
	x = SCREEN_WIDTH/2 - width/2
	y = SCREEN_HEIGHT/2 - height/2
	libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
	#present the root console to the player and wait for a key-press
	libtcod.console_flush()
	key = libtcod.console_wait_for_keypress(True)
	index = key.c - ord('a')
	if index >= 0 and index < len(options): return index
	return None


def inventory_menu(header):
	#show a menu with each itme of the inventory as an option
	if len(inventory) == 0:
		options = ["inventory is empty."]
	else:
		options = [item.name for item in inventory]

	index = menu(header, options, INVENTORY_WIDTH)
	if index is None or len(inventory) == 0: return None
	return inventory[index].item

def handle_keys():
	"""Handle_keys reads keypresses from the player while in console mode"""
	global key
	#no longer required with creation of player object
#	global playerx, playery
	global fov_map
	global fov_recompute
	#wait for keypress makes us turn based
	
	#this would be useful for a keyboard only game
	#key = libtcod.console_wait_for_keypress(True)

	#function keys
	if key.vk == libtcod.KEY_ENTER and key.lalt:
		#alt-enter toggles fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
	elif key.vk == libtcod.KEY_ESCAPE:
		#escape key exits game function
		return 'exit' 
	
	if game_state == 'playing':
		#movement keys
		if key.vk == libtcod.KEY_UP:
			player_move_or_attack(0,-1)
			fov_recompute = True
		elif key.vk == libtcod.KEY_DOWN:
			player_move_or_attack(0,1)
			fov_recompute = True
		elif key.vk == libtcod.KEY_LEFT:
			player_move_or_attack(-1,0)
			fov_recompute = True
		elif key.vk == libtcod.KEY_RIGHT:
			player_move_or_attack(1,0)
			fov_recompute = True
		else:
			#test for other keys
			key_char = chr(key.c)

			if key_char == 'g':
				#pick up an item
				for object in objects: #look for item in players tile
					if object.x == player.x and object.y == player.y and object.item:
						object.item.pick_up()
						break
			if key_char == 'i':
				chosen_item = inventory_menu('press the key next to an item to use it, or any other key to cancel.\n')
				if chosen_item is not None:
					chosen_item.use()

			if key_char == 'd':
				chosen_item = inventory_menu('ress the key next to the item to drop, or any other key to cancel\n')
				if chosen_item is not None:
					chosen_item.drop(player.x, player.y)

			return 'didnt-take-turn'

def target_monster(max_range=None):
	while True:
		(x,y) = target_tile(max_range)
		if x is None: return None
		for obj in objects:
			if obj.x == x and obj.y == y and obj.fighter and obj != player:
				return obj
def target_tile(max_range=None):
	#return the position of a tile left-click in players FOV, optionally limited by range, or None,None if rieght clicked
	global key, mouse
	while True:
		#render screen(erasing inv and show the names of obj under mouse as usual
		libtcod.console_flush()
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key,mouse)
		render_all()

		(x, y) = (mouse.cx, mouse.cy)

		if mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and (max_range is None or player.distance(x,y) <= max_range):
			return (x,y)
		if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
			return (None, None) #this cancels for right click or escape


def get_names_under_mouse():
	global mouse
	#return a string with the names of all objects under the mouse
	(x,y) = (mouse.cx, mouse.cy)
	names = [obj.name for obj in objects
		if obj.x == x and obj.y ==y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]
	names = ', '.join(names) #join the names, separated by commas
	return names.capitalize()

def player_death(player):
	#the game ended!
	global game_state
	message('You Died!', libtcod.red)
	game_state = 'dead'

	#for added affect, transform player into corpse
	player.char = '%'
	player.color = libtcod.dark_red

def monster_death(monster):
	#makes a corpse, which does not block move or attack
	message(monster.name.capitalize() + ' is dead!', libtcod.green)
	monster.char = '%'
	monster.color = libtcod.dark_red
	monster.blocks = False
	monster.fighter = None
	monster.ai = None
	monster.name = 'remains of ' + monster.name
	monster.send_to_back()

def render_bar(x,y, total_width, name, value, maximum, bar_color, back_color):
	#render a bar... first calculate it's width
	bar_width = int(float(value) / maximum * total_width)
	#then render the names under the mouse
	libtcod.console_set_default_foreground(panel, libtcod.light_grey)
	libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())
	#then render background
	libtcod.console_set_default_background(panel, back_color)
	libtcod.console_rect(panel, x,y,total_width,1, False, libtcod.BKGND_SCREEN)
	#then render bar on op
	libtcod.console_set_default_background(panel, bar_color)
	if bar_width > 0:
		libtcod.console_rect(panel,x,y,bar_width,1,False,libtcod.BKGND_SCREEN)
	#and put numerical representation as well
	libtcod.console_set_default_foreground(panel, libtcod.white)
	
	#libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER, name + ': ' + str(value) + '/' + str(maximum))	

def message(new_msg, color = libtcod.white):
	#plit the message if necessary, among multiple lines
	new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

	for line in new_msg_lines:
		#iff the buffer is full remove the first line to make room for the new one
		if len(game_msgs) == MSG_HEIGHT:
			del game_msgs[0]

		#add the new line as a tuple, with the text and the color
		game_msgs.append( (line, color) )
########################################################
# INITIALIZATION AND MAIN LOOP
########################################################

libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)
con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
libtcod.sys_set_fps(LIMIT_FPS)
#the coords here are the player starting location
fighter_component = Fighter(hp=30, defense=2, power=5, death_function=player_death)
player = Object(0, 0, '@', 'Seth', libtcod.white, blocks=True, fighter=fighter_component)
npc = Object(SCREEN_WIDTH/2-5, SCREEN_HEIGHT/2, '&', 'Chuckes', libtcod.red, blocks=True)
objects = [player, npc]

#generate starting map
make_map()

fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
for y in range(MAP_HEIGHT):
	for x in range(MAP_WIDTH):
		libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)
fov_recompute = False

panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

inventory = []
game_msgs = []

message("Welcome stranger!  Prepare to perish in the Tombs of the Ancient Kings.", libtcod.red)

mouse = libtcod.Mouse()
key = libtcod.Key()

#######################################################
#     The Main Loop!
#######################################################
while not libtcod.console_is_window_closed():

	libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
	#render the screen
	render_all()
	libtcod.console_flush()
	#erase obj at old loc before they move
	for object in objects:
		object.clear()
	player_action = handle_keys()
	if player_action == 'exit':
		break
	if game_state == 'playing' and player_action != 'didnt-take-turn':
		for object in objects:
			if object != player:
				if object.ai:
					object.ai.take_turn()

