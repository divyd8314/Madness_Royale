import pygame
from pygame import mixer 
import os
import random
import csv
import button 

# Initialize Pygame
mixer.init()
pygame.init()

# Set up display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Meme_Madness')

#setting frame rate
clock = pygame.time.Clock()
FPS = 60 #number of frames rendered each second 

#define game variables
score = [] #even though the new level will update, the coins will still be stored 
test_score = [0]
GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVELS = 3
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False 
start_intro = False 

#define player action variables
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False


#loading music 
pygame.mixer.music.load('audio/music.mp3')
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 5000)

jump_fx = pygame.mixer.Sound('audio/jump.flac')
jump_fx.set_volume(0.5)

shot_fx = pygame.mixer.Sound('audio/rifle.wav')
shot_fx.set_volume(0.5)

hurt_fx = pygame.mixer.Sound('audio/hurt.flac')
hurt_fx.set_volume(0.5)

grenade_fx = pygame.mixer.Sound('audio/explosion.ogg')
grenade_fx.set_volume(0.5)

power_up = pygame.mixer.Sound('audio/power_up.wav')
power_up.set_volume(1.0)

coin_pickup = pygame.mixer.Sound('audio/coin.wav')
coin_pickup.set_volume(0.5)

#load images
#button image
start_img = pygame.image.load('images/start_btn.png').convert_alpha()
exit_img = pygame.image.load('images/exit_btn.png').convert_alpha()
restart_btn = pygame.image.load('images/restart_btn.png').convert_alpha()
    
                     
#background image
back_img = pygame.image.load('images/Background/background.png').convert_alpha()

#store tiles in a list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'images/tile/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)
 
#bullet
bullet_img = pygame.image.load('images/bullet.png').convert_alpha()
#coins
coin_img = pygame.image.load('images/coinbox.png').convert_alpha()
#grenade
grenade_img = pygame.image.load('images/grenade.png').convert_alpha()
#pick up boxes
ammo_box = pygame.image.load('images/ammobox.png').convert_alpha()
grenade_box = pygame.image.load('images/grenadebox.png').convert_alpha()
coin_box = pygame.image.load('images/coinbox.png').convert_alpha()
item_boxes = {
  'Ammo' : ammo_box,
  'Grenade' : grenade_box,
  'Coins': coin_box
}

#define colours
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)

#defining the font
font = pygame.font.SysFont('Futura', 20)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def draw_bg():
    bgX = 0
    bgX -= 1.4  # Move both background images back
    if bgX < back_img.get_width() * -1:  # If our bg is at the -width then reset its position
        bgX = back_img.get_width()
    screen.blit(back_img, (bgX, -300))  
        

#function which resets the levels
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()
    
    #create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)
    return data 


class Char(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo, grenades, coins):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.shoot_cooldown = 0 #limits how quickly bullets fire
        self.grenades = grenades
        self.coins = coins
        self.health = 100
        self.max_health = self.health
        self.direction = 1 #looking to the right 
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False #Will flip the image if travelling left
        self.animation_list = []
        self.frame_index = 0
        self.action = 0 #0 = standing
        self.update_time = pygame.time.get_ticks()
  
        #variables only for the AI, in this case will only work for enemies 
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0
        
        #Load images for players
        animation_types = ["idle", "run", "attack", "death"]
        for animation in animation_types:
            #resetting the list of images 
            temp_list = []
            #number of files in each folder 
            num_of_frames = len(os.listdir(f'images/{self.char_type}/{animation}'))
   
            for i in range(num_of_frames):
                img = pygame.image.load(f'images/{self.char_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()


    def update(self):
        self.update_animation()
        self.check_alive()
        #update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1


    def move(self, moving_left, moving_right):
        #reset the variables once they move
        screen_scroll = 0
        dx = 0 #delta x
        dy = 0 #delta y

        #player moving variables if they are moving left or right 
        if moving_left:
            dx = -self.speed #x coordinate decreases 
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed #x coordinate increases
            self.flip = False
            self.direction = 1

        #jump
        if self.jump == True and self.in_air == False:
            self.vel_y = -13 #jumping upwards
            self.jump = False
            self.in_air = True

        #gravity so that player jumps and comes back down
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y #max velocity, will not go too low
        dy += self.vel_y

        #check for collision
        for tile in world.obstacle_list:
            #check collision in the x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                #if the ai has hit a wall then make it turn around
                if self.char_type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
            #check for collision in the y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                #check if jumping
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                #check if falling back down 
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom
        
        #if player collides with water 
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0
            hurt_fx.play()
            
        #check if player reaches the end tile of game , collision check
        level_complete = False 
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True 
        
        #if player falls off the tiles 
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0 
            hurt_fx.play()
            
        #check if going off the edges of the screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        #update rectangle position
        self.rect.x += dx
        self.rect.y += dy

        #update scroll based on where the player is 
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH)\
                or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx
        return screen_scroll, level_complete

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
            bullet_group.add(bullet)
            #reducing the ammo
            self.ammo -= 1


    def ai(self):
        #AI movement
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 300) == 1:
                self.update_action(0) #animation for idle state 
                self.idling = True
                self.idling_counter = 50
            #check if ai is near the player 
            if self.vision.colliderect(player.rect):
                #stop running and face the player
                self.update_action(0)#animation for idle state 
                #shoot
                self.shoot()
            else:
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)#animation for run
                    self.move_counter += 1
                    #update ai vision if the enemy moves in direction
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1 #counting down before ai moves again 
                    if self.idling_counter <= 0:
                        self.idling = False

        #scroll
        self.rect.x += screen_scroll


    def update_animation(self):
        #update animation
        ANIMATION_COOLDOWN = 100 #how long it takes to change animation
        #updating image depending on the frame 
        self.image = self.animation_list[self.action][self.frame_index]
        #checking if enough time has passed since the last animation update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        #if the animation is over, reset it to the first frame
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3: 
                self.frame_index = len(self.animation_list[self.action]) - 1 #stops the animation when character dies 
            else:
                self.frame_index = 0  #resets frame if char is idle or running/jumping



    def update_action(self, new_action):
        #check if the new action is different to the previous one
        if new_action != self.action:
            self.action = new_action
            #update the animation 
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()



    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)


    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)  #display image 


class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        #iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile >= 9 and tile <= 10:
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    elif tile >= 11 and tile <= 14:
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15:#create the player 
                        player =  Char('player', x * TILE_SIZE, y * TILE_SIZE, 2, 5, 20, 5, 0)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16:#create the enemy
                        enemy = Char('Enemy', x * TILE_SIZE, y * TILE_SIZE, 2, 2, 20, 0, 0)
                        enemy_group.add(enemy)
                    elif tile == 17:#create ammo box
                        item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 18:#create coins 
                        item_box = ItemBox('Coins', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19:#create grenade box
                        item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20: #create the exit
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)
            
                    
        return player, health_bar


    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])


class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))


    def update(self):
        #scroll
        self.rect.x += screen_scroll
        #check if the player has picked up the box
        if pygame.sprite.collide_rect(self, player):
            #check the type of box picked up
            if self.item_type == 'Coins':
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health
                player.coins += 1 
                coin_pickup.play()
            elif self.item_type == 'Grenade':
                player.grenades += 3
            elif self.item_type == 'Ammo':
                player.ammo += 15
            #delete the item box
            self.kill()


class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        #draw health bar
        self.health = health
        #calculate health ratio
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        #moving the bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll
        #checking if the bullet has gone off the screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        #collison with levels 
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        #checking for collisions with other players or enemies 
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 5
                hurt_fx.play()
                self.kill()
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 25
                    self.kill()



class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.vel_y = -12
        self.speed = 7
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction

    def update(self):
        #moving the grenade
        self.vel_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.vel_y

        #check for collision with level
        for tile in world.obstacle_list:
            #check collision with walls
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed
            #check for collision in the y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0
                #check if thrown up
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                #check if thrown down 
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom	


        #updating the position of the grenade 
        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        #countdown timer
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            grenade_fx.play()
            explosion = Explosion(self.rect.x, self.rect.y, 0.5)
            explosion_group.add(explosion)
            #grenade collison detection, do damage 
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
                abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
                player.health -= 50
            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
                    abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
                    enemy.health -= 50



class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(50):
            img = pygame.image.load(f'images/explosion/tile0{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        #scroll
        self.rect.x += screen_scroll

        #animating the explosion
        EXPLOSION_SPEED = 2
        #update explosion amimation
        self.counter += 1

        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            #if animation frames are done, then delete explosion
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]
class ScreenFade():
    def __init__(self, direction, colour, speed):
        self.direction = direction
        self.colour = colour
        self.speed = speed 
        self.fade_counter = 0
    
    def fade(self):
        fade_complete = False 
        self.fade_counter += self.speed
        if self.direction == 1: #a whole screen fade 
            pygame.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, SCREEN_WIDTH//2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour, (SCREEN_WIDTH//2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT//2))
            pygame.draw.rect(screen, self.colour, (0, SCREEN_HEIGHT//2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.direction == 2: #fade down when there is a vertical screen fade 
            pygame.draw.rect(screen, self.colour, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True 
        return fade_complete

#create screen fades 
fade_1 = ScreenFade(1, BLACK, 4)
death_fade = ScreenFade(2, PINK, 4)

#create buttons 
start_button = button.Button(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 150, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 + 10, SCREEN_HEIGHT // 2 - 150, exit_img, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_btn, 2)


#create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

collect_coin_executed = False

def collect_coin(coin):
    # print(coin)
    test_score = [0]
    test_score[0] += coin
    print(test_score[0])
    with open('scores.csv', 'a', newline = '') as csvfile:
        my_writer = csv.writer(csvfile, delimiter = ',')
        my_writer.writerow(test_score)
#create empty tile list
world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)
#load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)


#main game loop
run = True
coin = 0
while run: #executes the game
    # restart_flag = False
    clock.tick(FPS) 
    if start_game == False:
        #draw the menu
        screen.blit(back_img, (0, 0))
        #add buttons 
        if start_button.draw(screen):
            start_game = True
            start_intro = True 
        if exit_button.draw(screen):
            run = False
    else:
        #update background
        draw_bg()
        #draw world 
        world.draw()
        #show player health
        health_bar.draw(player.health)
        #show ammo
        draw_text('AMMO: ', font, WHITE, 10, 35)
        for x in range(player.ammo):
            screen.blit(bullet_img, (100 + (x * 13), 45))
        #show grenades
        draw_text('GRENADES: ', font, WHITE, 10, 60)
        for x in range(player.grenades):
            screen.blit(grenade_img, (130 + (x * 24), 56))
        #show coins
        draw_text('COINS: ', font, WHITE, 10, 85)
        for x in range(player.coins):
            screen.blit(coin_img, (85 + (x*15), 90))


        player.update()
        player.draw()

        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()

        #update and draw groups
        bullet_group.update()
        grenade_group.update()
        explosion_group.update()
        item_box_group.update()
        decoration_group.update()
        water_group.update()
        exit_group.update()
    
        bullet_group.draw(screen)
        grenade_group.draw(screen)
        explosion_group.draw(screen)
        item_box_group.draw(screen)
        decoration_group.draw(screen)
        water_group.draw(screen)
        exit_group.draw(screen)
        
        #show the intro
        if start_intro == True:
            if fade_1.fade():
                start_intro = False 
                fade_1.fade_counter = 0

        #update player actions
        if player.alive:
            #shoot bullets
            if shoot:
                player.shoot()
            #throw grenades
            elif grenade and grenade_thrown == False and player.grenades > 0:
                grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction),\
                            player.rect.top, player.direction)
                grenade_group.add(grenade)
                #Grenades decrease after thrown
                player.grenades -= 1
                grenade_thrown = True
            if player.in_air:
                player.update_action(2)#2 = jump/attack
            elif moving_left or moving_right:
                player.update_action(1) #1 = run
            else:
                player.update_action(0) #0 = idle 
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll
            #check if the level has been completed 
            if level_complete == True:
                power_up.play()
                start_intro = True 
                coin += player.coins
                level+=1
                bg_scroll = 0
                world_data = reset_level()
                if level <= MAX_LEVELS:
                     #load in level data and create world
                        with open(f'level{level}_data.csv', newline='') as csvfile:
                            reader = csv.reader(csvfile, delimiter=',')
                            for x, row in enumerate(reader):
                                for y, tile in enumerate(row):
                                    world_data[x][y] = int(tile)
                        world = World()
                        player, health_bar = world.process_data(world_data)
                else:
                    print("test")
                    score.append(coin)
                    with open('scores.csv', 'w', newline = '') as csvfile:
                        my_writer = csv.writer(csvfile, delimiter = ' ')
                        my_writer.writerow(score)
                    run = False                      
        else:
            #call function
            coin += player.coins
            if not collect_coin_executed: #in order to make this function only happen once rather than multiple times due to while loop
                collect_coin(coin)
                collect_coin_executed = True
                    
            coin = 0
            screen_scroll = 0 
            if death_fade.fade():
                if restart_button.draw(screen):
                    collect_coin_executed = False
                    death_fade.fade_counter = 0
                    start_intro = True 
                    bg_scroll = 0
                    world_data = reset_level()
                    #load in level data and create world
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)
  
    # Handle events
    for event in pygame.event.get():
        #quit game
        if event.type == pygame.QUIT:
            run = False
        #keyboard presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                moving_left = True
            if event.key == pygame.K_RIGHT:
                moving_right = True
            if event.key == pygame.K_a:
                shoot = True
                shot_fx.play()
            if event.key == pygame.K_s:
                grenade = True
            if event.key == pygame.K_SPACE and player.alive:
                player.jump = True
                jump_fx.play()
            if event.key == pygame.K_RETURN:
                run = False


        #keyboard button released
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                moving_left = False
            if event.key == pygame.K_RIGHT:
                moving_right = False
            if event.key == pygame.K_a:
                shoot = False
            if event.key == pygame.K_s:
                grenade = False
                grenade_thrown = False


    pygame.display.update()

pygame.quit()