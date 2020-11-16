import tcod, math, textwrap, tcod.event, shelve, heapq

heap = []
SCREEN_WIDTH = 120
SCREEN_HEIGHT = 50
MAP_WIDTH = 80
MAP_HEIGHT = 45
LIMIT_FPS = 30
ROOM_MAX_SIZE = 15
ROOM_MIN_SIZE = 4
MAX_ROOMS = 30
FOV_ALGO = 6
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10
MAX_ROOM_MONSTERS = 1
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1
color_dark_wall = tcod.Color(0,0,100)
color_light_wall = tcod.Color(130, 110, 50)
color_dark_ground = tcod.Color(50, 50 ,150)
color_light_ground = tcod.Color(200, 180, 50)
game_state = 'playing'
player_action = None
MAX_ROOM_ITEMS = 4
INVENTORY_WIDTH = 50
fullscreen = False
con = tcod.console_new(SCREEN_WIDTH,SCREEN_HEIGHT)
panel = tcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)
turn_counter = 0
status_objects = []

class Object:
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color, blocks=False, fighter=None, ai=None, Item=None, always_visible=False, speed=None, 
    action_points=None, Equipment = None, Status = None, no_fog = False):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.Item = Item
        self.fighter = fighter
        self.always_visible = always_visible
        self.speed = speed
        self.action_points = action_points
        self.Equipment = Equipment
        self.Status = Status
        self.no_fog = no_fog
        
        if self.fighter:  #let the fighter component know who owns it
            self.fighter.owner = self
 
        self.ai = ai
        if self.ai:  #let the AI component know who owns it
            self.ai.owner = self


        if self.Item:
            self.Item.owner = self 
        if self.Equipment:
            self.Equipment.owner = self
        if self.Status:
            self.Status.owner = self

    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        if not is_blocked(self.x + dx,self.y + dy):
            self.x += dx
            self.y += dy
        if map[self.x][self.y].Status is not None:
            map[self.x][self.y].Status.status_effect(self)
            status_objects.append(self)
    def move_noblock(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        self.x += dx
        self.y += dy
    def draw(self):
        #only show if it's visible to the player
        if tcod.map_is_in_fov(fov_map, self.x, self.y) or (self.always_visible and map[self.x][self.y].explored) or self.no_fog is True:
            #set the color and then draw the character that represents this object at its position
            tcod.console_set_default_foreground(con, self.color)
            tcod.console_put_char(con, self.x, self.y, self.char, tcod.BKGND_NONE)
    def draw_ignore_fog(self):
       
            #set the color and then draw the character that represents this object at its position
        tcod.console_set_default_foreground(con, self.color)
        tcod.console_put_char(con, self.x, self.y, self.char, tcod.BKGND_NONE)
    def clear(self):
        #erase the character that represents this object
        tcod.console_put_char(con, self.x, self.y, ' ', tcod.BKGND_NONE)
    def move_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2+ dy ** 2)
 
        dx = int(round(dx / distance))
        dy = int (round(dy / distance))
        self.move(dx, dy)
    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)
  

    def send_to_back(self):
        global objects
        objects.remove(self)
        objects.insert(0,self)
    def look(self):
        global cursor
        global fov_recompute
        objects.append(cursor)
        self.x = player.x
        self.y = player.y
        z = True
        while z is True:
            for event in tcod.event.wait():
                print(event)
                if event.type == 'KEYDOWN':
                    if event.scancode == tcod.event.SCANCODE_UP:
                        self.move_noblock(0,-1)
                        for object in objects:
                            if object != player:
                                object.draw()
                        player.draw()
                        Object.draw_ignore_fog(self)
                        tcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
                        tcod.console_blit(panel, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, PANEL_Y)
                        tcod.console_flush()
                        for object in objects:
                            object.clear()
                       
                    elif event.scancode == tcod.event.SCANCODE_DOWN:
                        self.move_noblock(0,1)
                        for object in objects:
                            if object != player:
                                object.draw()
                        player.draw()
                        Object.draw_ignore_fog(self)
                        tcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
                        tcod.console_blit(panel, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, PANEL_Y)
                        tcod.console_flush()
                        for object in objects:
                            object.clear()
                    elif event.scancode == tcod.event.SCANCODE_LEFT:
                        self.move_noblock(-1, 0)
                        for object in objects:
                            if object != player:
                                object.draw()
                        player.draw()
                        Object.draw_ignore_fog(self)
                        tcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
                        tcod.console_blit(panel, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, PANEL_Y)
                        tcod.console_flush()
                        for object in objects:
                            object.clear()
                    elif event.scancode == tcod.event.SCANCODE_RIGHT:
                        self.move_noblock(1,0)
                        for object in objects:
                            if object != player:
                                object.draw()
                        player.draw()
                        Object.draw_ignore_fog(self)
                        tcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
                        tcod.console_blit(panel, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, PANEL_Y)
                        tcod.console_flush()
                        for object in objects:
                            object.clear()
                    elif event.scancode == tcod.event.SCANCODE_O:
                        print (event)
                    elif event.scancode == tcod.event.SCANCODE_ESCAPE:
                        z = False
                        objects.remove(self)
                        break
                    elif event.scancode == tcod.event.SCANCODE_RETURN:
                        return (self.x, self.y)
                        z = False
                        break
        
        

    def move_astar (self, target):
        fov = tcod.map_new(MAP_WIDTH, MAP_HEIGHT)
        for y1 in range (MAP_HEIGHT):
            for x1 in range (MAP_WIDTH):
                tcod.map_set_properties(fov, x1, y1, not map[x1][y1].block_sight, not map[x1][y1].blocked)
        for object in objects:
                if object.blocks and object != self and object != target:
                    tcod.map_set_properties(fov, object.x, object.y, True, False)
        my_path = tcod.path_new_using_map(fov, 1.0)
        tcod.path_compute(my_path, self.x, self.y, target.x, target.y)
        if not tcod.path_is_empty(my_path) and tcod.path_size(my_path) < 25:
            x, y = tcod.path_walk(my_path,True)
            if x or y:
                self.x = x
                self.y = y
            else:
                self.move_towards(target.x, target.y)
            tcod.path_delete(my_path)
        if map[self.x][self.y].Status is not None:
            map[self.x][self.y].Status.status_effect(self)
            status_objects.append(self)
    def refresh_action(self):
        if self.action_points is not None:
            if self.action_points > 0:
                self.action_points -= 1000
def shoot(self):
    message('Shoot what tile?',tcod.white)
    render_all()
    tcod.console_flush()
    Object.look(cursor)
    line = tcod.los.bresenham((player.x, player.y), (cursor.x, cursor.y)).tolist()
    valid_target = False
    c = 0
    for i in line:
        if valid_target is True:
            break
        line_x = i[0]
        line_y = i[1]
        if c == 0:
            c+=1 
            continue
        if is_blocked(line_x, line_y) is True:
            for object in objects:
                if line_x == object.x and line_y == object.y and object.fighter:
                    self.fighter.shoot_attack(object)
                    valid_target = True
                    break
            if c == 1:
                continue
            valid_target = True
        c+=1
                    


     
    
    try:
        objects.remove(cursor)
        player.action_points += player.speed
    except:
        print('Fire cancelled')

            

            

class Status:
    global turn_counter, fov_recompute
    def __init__(self, duration, status_effect, status_clear_function, end_time = None, dot = False ):
        self.duration = duration 
        self.end_time = duration+turn_counter
        self.status_effect = status_effect
        self.status_clear_function = status_clear_function
        self.dot = dot
        
        
        
    def burning_clear(self):
        self.Status = None
    def burning(self):
        damage = 3
        if self.fighter is not None and self.Status is not None:
            self.fighter.take_damage(damage)
            message (self.name.capitalize() + ' takes ' + str(damage) + ' from fire!')
    def tile_burning(self):
        on_fire = Status(4,Status.burning,Status.burning_clear,dot = True)
        self.Status = on_fire
    def tile_burning_clear(self):
        self.color = color_light_ground
        self.Status = None
    def clear(object):
        object.Status.status_clear_function(object)  

    def fast(self):
        self.speed -= 500
        
    def random_teleport():
        global fov_recompute, player
        inventory[item_selection].Item.user = player
        x = tcod.random_get_int(0,0,MAP_WIDTH)
        y = tcod.random_get_int(0,0,MAP_HEIGHT)
        while is_blocked(x,y):
            x = tcod.random_get_int(0, 0, MAP_WIDTH)
            y = tcod.random_get_int(0, 0, MAP_HEIGHT)
        player.x = x
        player.y = y
        fov_recompute = True
        render_all()
        tcod.console_flush()
        for object in objects:
            object.clear()
    def fast_clear(self):
        self.speed += 500
    def accurate(self):
        self.fighter.accuracy += 20
        self.fighter.shoot_accuracy += 20
    def accurate_clear(self):
        self.fighter.accuracy -= 20
        self.fighter.shoot_accuracy -= 20
    def Sensed(self):
        Sensed = Status(4, 'No_fog', status_clear_function = Status.temp_telepathy_clear)
        self.no_fog = True
        self.Status = Sensed
    def Detected(self):
        Detected = Status(4, 'Detected', status_clear_function = Status.object_detection_clear)
        self.no_fog = True
        self.Status = Detected
    def temp_telepathy():
        for object in objects:
            if object.ai:
                object = Status.Sensed(object)
                status_objects.append(object)
    def object_detection():
        for object in objects:
            if object.Item:
                object = Status.Detected(object)
    def object_detection_clear(object):
        object.Status = None
    def temp_telepathy_clear(object):
            object.no_fog = False
            object.Status = None
    def time_stop(self):
        global player_old_speed
        player_old_speed = self.speed
        self.action_points = 0
        self.speed = 0
    def time_stop_clear(self):
        self.speed = player_old_speed
    def poison(self):
        damage = 4
        if self.fighter is not None and self.Status is not None:
            self.fighter.take_damage(damage)
            message (self.name.capitalize() + ' takes ' + str(damage) + ' from poison!')
    def webbed_clear(self):
        self.Status = None
            
    def poison_clear(self):
        #doesnt have to do anything?
        self.Status = None
    def slow(self, slow_amount, action_points):
        self.speed = slow_amount
        self.action_points = action_points
    def slow_clear(self):
        self.action_points = 0
        self.speed = self.Status.status_effect



              
class Tile:
    def __init__(self, blocked, color = color_light_ground, block_sight = None, Status = None):
        self.blocked = blocked
        self.explored = False
        self.color = color
        #by default if tile is blocked, blocks sight
        if block_sight is None: block_sight=blocked
        self.block_sight = block_sight
        self.Status = Status
 
class Fighter:
    def __init__(self, hp, defense, power, accuracy, shoot_accuracy = 0, death_function=None, shoot_power = 0, will = 0, dodge = 0):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function
        self.shoot_power = shoot_power
        self.will = will
        self.dodge = dodge
        self.accuracy = accuracy
        self.shoot_accuracy = shoot_accuracy
    def attack(self, target):
        hit_chance = self.accuracy - target.fighter.dodge
        hit_roll = tcod.random_get_int(0,0,100)
        damage = self.power - target.fighter.defense
        if hit_roll > hit_chance:
            message (self.owner.name.capitalize() + ' attacks ' + target.name + ' but misses!')
        
        elif damage > 0:
            #make the target take some damage
            message (self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage)
        
            
        else:
            message (self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')
    def shoot_attack(self, target):
        hit_chance = self.shoot_accuracy - target.fighter.dodge
        hit_roll = tcod.random_get_int(0,0,100)
        damage = self.shoot_power - target.fighter.defense
        if hit_roll > hit_chance:
            message (self.owner.name.capitalize() + ' shoots ' + target.name + ' but misses!')
        elif damage > 0:
            #make the target take some damage
            message (self.owner.name.capitalize() + ' shoots ' + target.name + ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage)
        else:
            message (self.owner.name.capitalize() + ' shoots ' + target.name + ' but it has no effect!')
    def take_damage (self, damage):
        if damage > 0:
            self.hp -= damage
        if self.hp <= 0:
            function = self.death_function
            if function is not None:
                function(self.owner)
    def heal (self, amount):
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
def player_death(player):
    global game_state
    message ('You died!')
    game_state = 'dead'
def monster_death(monster):
    monster.char = '%'
    monster.color = tcod.white
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.send_to_back
    monster.action_points = None
 
class BasicMonster:
    def take_turn(self):
        monster = self.owner
        if tcod.map_is_in_fov(fov_map, monster.x, monster.y):
            if monster.distance_to(player) >= 2:
                if monster.Status is None or monster.Status.status_effect is not 'Webbed':
                    monster.move_astar(player)
            elif player.fighter.hp > 0:
                    monster.fighter.attack(player)  
        monster.action_points += monster.speed
def aoe_check(radius,map_check = False):
    global targets, map_targets
    targets = []
    map_targets = []
    los_blocked = False
    c=0
    for object in objects:
        if Object.distance_to(object, cursor) <= radius and object.fighter:
            line = tcod.los.bresenham((cursor.x, cursor.y), (object.x, object.y)).tolist()
            for i in line:
                if c == 0:
                    c+=1
                    continue
                line_x = i[0]
                line_y = i[1]
                if is_blocked(line_x, line_y, monster_check = False):
                    los_blocked = True
            if los_blocked is True:
                break
            else:
                if object.fighter:
                    targets.append(object)
    if map_check is not False:
        for x in range ((radius*2+1)):
            for y in range ((radius*2+1)):
                #if map[cursor.x-2][cursor.y-2] is Tile:
                map_targets.append(map[cursor.x+x-radius][cursor.y+y-radius])
            
def grenade_cleanup(self):
        try:
            targets.clear()
            objects.remove(cursor)
            player.action_points += player.speed
            inventory.remove(self.owner)
        except:
            print('Fire cancelled')
def grenade_toss():
    message('Attack what tile?',tcod.white)
    render_all()
    tcod.console_flush()
    Object.look(cursor)
    
class Item:
    def __init__ (self, use_function = None, throw_function = None, user = None):
        
       
        self.use_function = use_function
        self.throw_function = throw_function
        self.user = user


    def use(self):
        if self.owner.Equipment:
            self.owner.Equipment.toggle_equip()
            return
        elif self.throw_function is not None:
            self.throw_function(self)
        elif self.use_function is None:
            message('The ' + self.owner.name + 'cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                inventory.remove(self.owner)
    def firestorm_grenade(self):
        grenade_toss()
        aoe_check(1, map_check=True)
        on_fire = Status(4,Status.burning,Status.burning_clear,dot = True)
        tile_burning = Status(4, Status.tile_burning, Status.tile_burning_clear)
        for target in targets:
            target.Status = on_fire
            status_objects.append(target)
        for map_target in map_targets:
            map_target.Status = tile_burning
            map_target.color = tcod.red
            status_objects.append(map_target)
        grenade_cleanup(self)
        map_targets.clear()
    def frag_grenade(self):
        grenade_toss()
        aoe_check(2)
        damage = 4
        for target in targets:
            target.fighter.take_damage(damage)
            message ('Frag grenade' + ' hits ' + target.name + ' for ' + str(damage) + ' hit points.')
        
        grenade_cleanup(self)
    def poison_grenade(self):
        grenade_toss()
        aoe_check(2)
        poison = Status(4, status_effect = Status.poison, status_clear_function= Status.poison_clear, dot = True)
        for target in targets:
            target.Status = poison
            status_objects.append(target)
        
        grenade_cleanup(self)
    def webbing_grenade(self):
        grenade_toss()
        aoe_check(3)
        Webbed = Status(4, 'Webbed', Status.webbed_clear)
        for target in targets:
            target.Status = Webbed
            status_objects.append(target)
        grenade_cleanup(self)

    def cast_heal():
        if user.fighter.hp == user.fighter.max_hp:
            message ('You are already at full health!', tcod.red)
            return 'cancelled'
 
        message('Your wounds closed.', tcod.light_violet)
        player.fighter.heal(4)
    def speed_up():
        Fast = Status(4,status_effect = Status.fast(inventory[item_selection].Item.user),status_clear_function = Status.fast_clear)
        inventory[item_selection].Item.user.Status = Fast
        status_objects.append(inventory[item_selection].Item.user)
    def accuracy_up():
        Accurate = Status(4, status_effect =  Status.accurate(inventory[item_selection].Item.user), status_clear_function = Status.accurate_clear)
        inventory[item_selection].Item.user.Status = Accurate
        status_objects.append(inventory[item_selection].Item.user)
    def time_stop_use():
        TimeStopped = Status(4, status_effect = Status.time_stop(inventory[item_selection].Item.user),status_clear_function = Status.time_stop_clear)
        inventory[item_selection].Item.user.Status = TimeStopped
        status_objects.append(inventory[item_selection].Item.user)
    def stasis_grenade(self):
        grenade_toss()
        aoe_check(2)
        for target in targets:
            Slow = Status(4, target.speed, status_clear_function= Status.slow_clear)
            target.Status = Slow
            Status.slow(target, 0, 500000)
            status_objects.append(target)
        grenade_cleanup(self)


 
    def pick_up(self):
        if len(inventory) >= 52:
            message('Your inventory is full!', tcod.white)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message('You picked up a ' + self.owner.name + '!', tcod.green)
    def drop(self):
        
        inventory.remove(self.owner)
        objects.append(self.owner)
  
        self.owner.x = player.x
        self.owner.y = player.y
 
class Equipment:
    global equipment
    def __init__ (self, slot):
        self.slot = slot
        self.is_equipped = False

    def toggle_equip(self):
        if self.is_equipped:
            self.unequip()
        else:
            self.equip()

    def equip(self):
        self.is_equipped = True
        message('Equipped ' + self.owner.name + ' on ' + self.slot + '.', tcod.light_green)   
        old_equipment = Equipment.slotequipped(self.slot)
        
        equipment.append(self)
        inventory.remove(self.owner)

        if old_equipment is not None:
            old_equipment.Equipment.unequip()
    def unequip(self):
        if not self.is_equipped: return
        self.is_equipped = False
        message('Unequipped ' + self.owner.name + ' from ' + self.slot + '.', tcod.yellow)
        equipment.remove(self)
        inventory.append(self.owner)           
    def slotequipped(slot):
        for obj in equipment:
            if obj.slot == slot and obj.is_equipped:
                return obj.owner
            return None 



    


 
 
 
def player_move_or_attack(dx, dy):
    global fov_recompute, action_points, speed
    x = player.x+dx
    y = player.y+dy
    speed = player.speed
    target = None
    for Object in objects:
        if Object.fighter and Object.x == x and Object.y == y:
            target = Object
            break
    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        fov_recompute = True
    player.action_points += player.speed
 
   
def handle_keys():
   
    global fov_recompute
    global player_action
   
    for event in tcod.event.wait():
        #print(event)  
        if game_state == 'playing':
                   
           
            if event.type == 'QUIT':
                raise SystemExit()
            elif event.type == 'KEYDOWN':
               
                if event.scancode == tcod.event.SCANCODE_UP:
                    player_move_or_attack(0, -1)
                    fov_recompute = True
                    
                elif event.scancode == tcod.event.SCANCODE_DOWN:
                    player_move_or_attack(0, 1)
                    fov_recompute = True
                   
                elif event.scancode == tcod.event.SCANCODE_LEFT:
                    player_move_or_attack(-1,0)
                    fov_recompute = True
                   
                elif event.scancode == tcod.event.SCANCODE_RIGHT:
                    player_move_or_attack(1, 0)
                    fov_recompute = True
                elif event.scancode == tcod.event.SCANCODE_PERIOD:
                    if stairs.x == player.x and stairs.y == player.y:
                        next_level()
               
                elif event.scancode == tcod.event.SCANCODE_G:
                    for object in objects:
                        if player.x == object.x and object.y == player.y and object.Item:
                            object.Item.pick_up()
                            picked_up = True
                            break
                        else:
                            picked_up = False
                    if picked_up is not True:
                        message('Nothing to pick up!')
                           
                elif event.scancode == tcod.event.SCANCODE_I:
                    inventory_menu('---INVENTORY---')
                elif event.scancode == tcod.event.SCANCODE_D:
                    inventory_menu_drop('---INVENTORY---')
                elif event.scancode == tcod.event.SCANCODE_E:
                    equipment_menu('---EQUIPMENT---')  
                elif event.scancode == tcod.event.SCANCODE_O:
                    print (event)
                elif event.scancode == tcod.event.SCANCODE_F:
                    shoot(player)
                elif event.scancode == tcod.event.SCANCODE_F10:
                    save_game()
                    raise SystemExit()
                elif event.scancode == tcod.event.SCANCODE_X:
                    Object.look(cursor)
            elif event.type != 'KEYDOWN':
               tcod.event.wait()
   
def next_level():
    global dungeon_level, map
    dungeon_level += 1
    objects.clear()
    map.clear()
    objects.append(player)
    make_map()
    for y in range (MAP_HEIGHT):
        for x in range (MAP_WIDTH):
            tcod.console_set_char_background(con, x, y, tcod.black, tcod.BKGND_SET)
    initialize_fov()
     
       
class Rect:
    #rectangle room
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x+w
        self.y2 = y+h
    def center(self):
        center_x=(self.x1+self.x2)//2
        center_y=(self.y1+self.y2)//2
        return (center_x, center_y)
    def intersect(self, other):
        #returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1
        and self.y1 <= other.y2 and self.y2 >=other.y1)
def createRoom(room):
    global map
    for x in range(room.x1+1, room.x2):
        for y in range(room.y1+1, room.y2+1):
            map[x][y].blocked=False
            map[x][y].block_sight=False
def createHTunnel(x1, x2, y):
    global map
    for x in range(min(x1, x2), max(x1, x2) +1):
        map[x][y].blocked=False
        map[x][y].block_sight=False
def createVTunnel(y1, y2, x):
    global map
    for y in range(min(y1, y2), max(y1, y2) +1):
        map[x][y].blocked=False
        map[x][y].block_sight=False
 
       
    def clear(self):
        #erase character
        tcod.console_put_char(con, self.x, self.y, ' ', tcod.BKGND_NONE)
 
 
 
def make_map():
    global map, stairs
 
    #fill map with "unblocked" tiles
    map = [
         [Tile(True) for y in range(MAP_HEIGHT)]
         for x in range(MAP_WIDTH)
    ]
    rooms = []
    num_rooms = 0
    for r in range(MAX_ROOMS):
        #random width and height
        w = tcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = tcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = tcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = tcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)
        newroom = Rect(x,y,w,h)
        failed = False
        for other_room in rooms:
            if newroom.intersect(other_room):
                failed = True
                break
        if not failed:
            createRoom(newroom)
            (new_x, new_y) = newroom.center()
 
            if num_rooms == 0:
                player.x = new_x
                player.y = new_y
            else:
                #all rooms after the first:
                #connect it to the previous room with a tunnel
 
                #center coordinates of previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()
 
                #draw a coin (random number that is either 0 or 1)
                if tcod.random_get_int(0, 0, 1) == 1:
                    #first move horizontally, then vertically
                    createHTunnel(prev_x, new_x, prev_y)
                    createVTunnel(prev_y, new_y, new_x)
                else:
                    #first move vertically, then horizontally
                    createVTunnel(prev_y, new_y, prev_x)
                    createHTunnel(prev_x, new_x, new_y)
 
            #finally, append the new room to the list
            place_objects(newroom)
            rooms.append(newroom)
            num_rooms += 1
                #create stairs at the center of the last room
    stairs = Object(new_x, new_y, '>', 'stairs', tcod.white, always_visible=True)
    objects.append(stairs)
    stairs.send_to_back()  #so it's drawn below the monsters
 
def render_all():
    global fov_map, color_dark_wall, color_light_wall
    global color_dark_ground, color_light_ground
    global fov_recompute
   
    #draw all in objects list
    if fov_recompute:
            #recompute FOV if needed (the player moved or something)
        fov_recompute = False
        tcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
        for y in range (MAP_HEIGHT):
            for x in range (MAP_WIDTH):
                visible = tcod.map_is_in_fov(fov_map,x,y)
                wall = map[x][y].block_sight
                if not visible:
                    if map[x][y].explored:
                        if wall:
                            tcod.console_set_char_background(con, x, y, color_dark_wall, tcod.BKGND_SET)
                        else:
                            tcod.console_set_char_background(con,x,y,color_dark_ground,tcod.BKGND_SET)
                else:
                    if wall:
                        tcod.console_set_char_background(con, x, y, color_light_wall, tcod.BKGND_SET)
                    else:
                        tcod.console_set_char_background(con,x,y,map[x][y].color,tcod.BKGND_SET)
                    map[x][y].explored=True
    #draw all objects in the list
    for object in objects:
        if object != player:
            object.draw()
    player.draw()
    #blit the contents of "con" to the root console
    tcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
    # GUI section
    tcod.console_set_default_background(panel, tcod.black)
    tcod.console_clear(panel)
 
    # Game messages
    y = 1
    for (line, color) in game_msgs:
        tcod.console_set_default_foreground(panel, color)
        tcod.console_print_ex(panel, MSG_X, y, tcod.BKGND_NONE, tcod.LEFT, line)
        y += 1
 
    # Player stats
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp, tcod.light_red, tcod.darker_red)
    tcod.console_print_ex(panel, 1,3,tcod.BKGND_NONE,tcod.LEFT,'Dungeon level ' + str(dungeon_level))
   
    # Blit con to root console
    tcod.console_blit(panel, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, PANEL_Y)
def is_blocked(x, y, monster_check = None):
    if map[x][y].blocked:
        return True
    for object in objects:
        if object.blocks and object.x == x and object.y == y and monster_check is None:
            return True
    return False


    

#MONSTER BLOCK
def troll():
    fighter_component = Fighter(16,1,4, death_function = monster_death, accuracy = 80)
    ai_component = BasicMonster()
    troll = Object(0,0,'T','troll', tcod.darker_green, blocks=True, fighter=fighter_component, ai=ai_component, action_points=0,speed=1000)
    return troll
def orc():
    fighter_component = Fighter(10,0,3, death_function = monster_death, accuracy = 50)
    ai_component = BasicMonster()
    orc = Object(0, 0, 'o', 'orc', tcod.desaturated_green, blocks=True, fighter=fighter_component ,ai=ai_component, action_points=0, speed=1000)
    return orc
monster_dict = {0:troll, 1:orc}
#ITEMS BLOCK
#CANISTERS
def healing_canister():
    healing_canister = Object(0,0,'!', 'healing canister', tcod.light_red,always_visible=True, Item=Item(use_function=Item.cast_heal))
    return healing_canister
def speed_canister():
    speed_canister = Object(0,0,'!', 'speed canister', tcod.green,always_visible=True, Item=Item(use_function=Item.speed_up))
    return speed_canister
def accuracy_canister():
    accuracy_canister = Object(0,0,'!', 'speed canister', tcod.yellow,always_visible=True, Item=Item(use_function=Item.accuracy_up))
    return accuracy_canister
def telepathy_canister():
    telepathy_canister = Object(0,0,'!', 'telepathy canister', tcod.red,always_visible=True, Item=Item(use_function=Status.temp_telepathy))
    return telepathy_canister
def displacement_canister():
    displacement_canister = Object(0,0,'!','displacement canister', tcod.light_green, always_visible = True, Item=Item(use_function = Status.random_teleport))
    return displacement_canister
def object_detection_canister():
    object_detection_canister = Object(0,0,'!','object detection canister',tcod.blue,always_visible = True, Item=Item(use_function = Status.object_detection))
    return object_detection_canister
def time_stop_canister():
    time_stop_canister = Object(0,0,'!','time stop canister',tcod.violet,always_visible = True, Item=Item(use_function = Item.time_stop_use))
    return time_stop_canister
#GRENADES
def frag_grenade():
    frag_grenade = Object(0,0,'*','frag_grenade',tcod.yellow, always_visible = True, Item=Item(throw_function = Item.frag_grenade))
    return frag_grenade
def poison_grenade():
    poison_grenade = Object(0,0,'*','poison grenade',tcod.light_green, always_visible = True, Item=Item(throw_function = Item.poison_grenade))
    return poison_grenade
def stasis_grenade():
    stasis_grenade = Object(0,0,'*','stasis grenade',tcod.purple, always_visible = True, Item=Item(throw_function = Item.stasis_grenade))
    return stasis_grenade
def webbing_grenade():
    webbing_grenade = Object(0,0,'*','webbing grenade',tcod.white, always_visible = True, Item=Item(throw_function = Item.webbing_grenade))
    return webbing_grenade
def firestorm_grenade():
    firestorm_grenade = Object(0,0,'*','firestorm grenade',tcod.red, always_visible = True, Item=Item(throw_function = Item.firestorm_grenade))
    return firestorm_grenade
#WEAPONS
def katana():
    katana = Object(0,0,'/','Katana',tcod.white, Item=Item(), Equipment=Equipment('right_hand'))
    return katana  



item_chances = (
    [0, katana],[0, healing_canister], [0, speed_canister], [0, accuracy_canister], [0, telepathy_canister], [0, displacement_canister], [0, object_detection_canister],
    [0, time_stop_canister], [0, frag_grenade], [0, poison_grenade], [0, stasis_grenade], [0, webbing_grenade], [100, firestorm_grenade]
)
monster_chances = ([80, orc],[20, troll])
item_table = []
monster_table = []
for number_items_chances in range(len(item_chances)):
    for item_chance in range(item_chances[number_items_chances][0]):
        item_table.append(item_chances[number_items_chances][1])
for number_monster_chances in range(len(monster_chances)):
    for monster_chance in range(monster_chances[number_monster_chances][0]):
        monster_table.append(monster_chances[number_monster_chances][1])

def place_objects(room):
    
    num_monsters = tcod.random_get_int(0,1, MAX_ROOM_MONSTERS)
    Item.always_visible = True
    for i in range (num_monsters):
        random_number = tcod.random_get_int(0,0,99)
        rng_monster = monster_table[random_number]()
        x = tcod.random_get_int(0, room.x1+1, room.x2-1)
        y = tcod.random_get_int(0, room.y1+1, room.y2-1)
        rng_monster.x = x
        rng_monster.y = y
        while is_blocked(x,y):
            x = tcod.random_get_int(0, room.x1+1, room.x2-1)
            y = tcod.random_get_int(0, room.y1+1, room.y2-1)
       
        
        objects.append(rng_monster)
  

    num_items = tcod.random_get_int(0,2,MAX_ROOM_ITEMS)
    for i in range(num_items):
        random_number = tcod.random_get_int(0,0,99)
        rng_item = item_table[random_number]()
        x = tcod.random_get_int(0, room.x1+1, room.x2-1)
        y = tcod.random_get_int(0, room.y1+1, room.y2-1)
        rng_item.x=x
        rng_item.y=y
        while is_blocked (x,y):
            x = tcod.random_get_int(0, room.x1+1, room.x2-1)
            y = tcod.random_get_int(0, room.y1+1, room.y2-1)
        
        objects.append(rng_item)
        rng_item.send_to_back()
def render_bar (x, y, total_width, name, value, maximum, bar_color, back_color):
    status_width = int(float(value) / maximum * total_width)
 
    # Render background
    tcod.console_set_default_background(panel, back_color)
    tcod.console_rect(panel, x, y, total_width, 1, False, tcod.BKGND_SCREEN)
 
    # Render bar
    tcod.console_set_default_background(panel, bar_color)
    if status_width > 0:
        tcod.console_rect(panel, x, y, status_width, 1, False, tcod.BKGND_SCREEN)
 
    # Render center text with values
    tcod.console_set_default_foreground(panel, tcod.white)
    stats = name + ': ' + str(value) + '/' + str(maximum)
    tcod.console_print_ex(panel, int(x + total_width / 2), y, tcod.BKGND_NONE, tcod.CENTER, stats)
 
def message(new_msg, color = tcod.white):
    #split the message if necessary, among multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
 
    for line in new_msg_lines:
        #if the buffer is full, remove the first line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]
 
        #add the new line as a tuple, with the text and the color
    game_msgs.append((line,color))
def menu(header,options,width):
    global key
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')
    header_height = tcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
    height = len(options) + header_height
    window = tcod.console_new(width, height)
    tcod.console_set_default_foreground(window, tcod.white)
    tcod.console_print_rect_ex(window, 0, 0, width, height, tcod.BKGND_NONE, tcod.LEFT, header)
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '('  + chr(letter_index) + ')' + option_text
        tcod.console_print_ex(window, 0 ,y ,tcod.BKGND_NONE, tcod.LEFT, text)
        y += 1
        letter_index += 1
    x = SCREEN_WIDTH*2//3 - width//2
    y = 5
    tcod.console_blit(window, 0, 0, width, height, 0, x,y)
    tcod.console_flush()
    key_wait()
   
   
def key_wait():
      global key
      for event in tcod.event.wait():
        print (event)
        if event.type != 'KEYDOWN':
            tcod.event.wait()
        else:
            #if event.type == 'TEXTINPUT':
            key = event.sym
           
            break
       
def main_menu():
    img = tcod.image_load('menu_background.png')
    while not tcod.console_is_window_closed():
        tcod.image_blit_2x(img, 0,0,0)
        menu('',['Play a new game', 'Continue last game', 'Quit'], 24)
 
        if key == 97:
            new_game()
            break
        elif key == 98:
            #try:
            load_game()
            break
            #except:
                #menu('No saved game to load.',[],24)
           
           
        elif key == 99:
            raise SystemExit()        
           
         
       
def inventory_menu(header):
    global item_selection, inventory
    if len(inventory) == 0:
        options =['You "don\'t have any items!']  
    else:
        options = [item.name for item in inventory]
    index = menu(header,options,INVENTORY_WIDTH)
    item_selection = key - ord('a')
    if item_selection >= 0 and item_selection < len(options):
        inventory[item_selection].Item.user = player
        inventory[item_selection].Item.use()
def equipment_menu(header):
    if len(equipment) == 0:
        options =['You "don\'t have any equipment!']  
    else:
        options = [item.owner.name for item in equipment]
    index = menu(header,options,INVENTORY_WIDTH)
    item_selection = key - ord('a')
    if item_selection >= 0 and item_selection < len(options):
        equipment[item_selection].toggle_equip()
 
def inventory_menu_drop(header):
    if len(inventory) == 0:
        options =['You "don\'t have any items!']  
    else:
        options = [item.name for item in inventory]
    index = menu(header,options,INVENTORY_WIDTH)
    item_selection = key - ord('a')
    if item_selection >= 0 and item_selection < len(options):
        inventory[item_selection].Item.drop()

def new_game():
    global player, inventory, game_msgs, game_state, objects, cursor, dungeon_level, equipment
 
    fighter_component = Fighter(5000,2,5, death_function = player_death, shoot_power = 4, accuracy = 100, dodge = 50, shoot_accuracy = 100)
    player = Object(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, '@','player', tcod.white, blocks=True, fighter=fighter_component, speed=1000, action_points=0)
    objects = [player]
   
    game_msgs = []
    cursor = Object(player.x, player.y, '_','look_cursor',tcod.green)
    dungeon_level = 1
    make_map()
    initialize_fov()
    inventory = []
    equipment = []

def save_game():
    file = shelve.open('savegame', 'n')
    file['map']=map
    file['objects']=objects
    file['player_index']=objects.index(player)
    file['game_state']=game_state
    file['game_msgs']=game_msgs
    file['inventory']=inventory
    file['stairs_index']=objects.index(stairs)
    file['dungeon_level']=dungeon_level
   
def load_game():
    global map, objects, player, inventory, game_msgs, game_state, stairs, dungeon_level
    file = shelve.open('savegame','r')
    objects = file['objects']
    player = objects[file['player_index']]  #get index of player in objects list and access it
    inventory = file['inventory']
    game_msgs = file['game_msgs']
    game_state = file['game_state']
    map = file['map']
    stairs = objects[file['stairs_index']]
    dungeon_level = file['dungeon_level']
    file.close()  
    initialize_fov()
 
def initialize_fov():
    global fov_recompute, fov_map
    fov_map = tcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            tcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)
    fov_recompute = True
 
font_path = 'terminal8x8_gs_tc.png'
tcod.console_set_custom_font(font_path, tcod.FONT_TYPE_GREYSCALE | tcod.FONT_LAYOUT_TCOD)
window_title = 'roguelike.py'
tcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, window_title, fullscreen)
tcod.sys_set_fps(LIMIT_FPS)
main_menu()
     
def heap_refresh():
    heap.clear()
    for xyz, object in enumerate(objects):
        if object.action_points is not None:
            heapq.heappush(heap,(object.action_points, xyz))

def check_status_effects():
    global turn_counter
    for object in status_objects:
        if object.Status is not None:
            if object.Status.end_time <= turn_counter:
                Status.clear(object)
                object.Status = None
            elif object.Status.dot is not False:
                    object.Status.status_effect(object)
        else:
            status_objects.remove(object)
            







def main():
    global player_x, player_y
    global player_action
    global objects
    global turn_counter
   
   
    while True:
        render_all()
        tcod.console_flush()
        for object in objects:
            object.clear()
            object.refresh_action()
        
        handle_keys()
        heap_refresh()
        for object in heap:
            while objects[heap[0][1]] is not player:
                objects[heap[0][1]].ai.take_turn() 
                if objects[heap[0][1]].action_points < player.action_points:
                    heapq.heappushpop(heap, (objects[heap[0][1]].action_points, heap[0][1]))
                else:
                    heapq.heappop(heap)

            break
            
        

        
        player_action = 'playing'
        check_status_effects()
        turn_counter += 1
main()