import pygame
from pygame import mixer
import os
import random
import csv
import button

mixer.init()
pygame.init()

# Get display resolution
display_info = pygame.display.Info()
SCREEN_WIDTH = display_info.current_w
SCREEN_HEIGHT = display_info.current_h

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption('Baucha')

bg_image = pygame.image.load("img/background/full bg.png").convert_alpha()
start_image = pygame.image.load("img/background/start_img.png").convert_alpha()

# set framerate
clock = pygame.time.Clock()
FPS = 70

# define game variables
GRAVITY = 0.75
SCROlL_THRESH = 500
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 22
MAX_LEVEL = 1
screen_scroll = 0
bg_scroll = 0
level = 0
start_game = False

# define player action variables
moving_left = False
moving_right = False
shoot = False
slash = False
grenade = False
grenade_thrown = False

# load music and sounds
pygame.mixer.music.load('audio/Elven Flute (Medieval Music).mp3')
pygame.mixer.music.set_volume(0.4)
pygame.mixer.music.play(-1, 0.0, 5000)
jump_fx = pygame.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0.2)
shot_fx = pygame.mixer.Sound('audio/fire.mp3')
shot_fx.set_volume(0.09)
grenade_fx = pygame.mixer.Sound('audio/grenade.wav')
grenade_fx.set_volume(0.5)
slash_fx = pygame.mixer.Sound('audio/Sword Slash-Sound Effect HD-[AudioTrimmer.com].mp3')
slash_fx.set_volume(0.5)
walking_fx = pygame.mixer.Sound('audio/Running On Grass Sound Effect-[AudioTrimmer.com].mp3')
walking_fx.set_volume(10)
eat_fx = pygame.mixer.Sound('audio/eating.mp3')
eat_fx.set_volume(0.1)
drinking_fx = pygame.mixer.Sound('audio/Drinking.mp3')
drinking_fx.set_volume(0.8)
water_fx = pygame.mixer.Sound('audio/water.mp3')
water_fx.set_volume(0.4)

# load image
# button images
start_img = pygame.image.load('img/start_btn.png').convert_alpha()
exit_img = pygame.image.load('img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()
# store tiles in a list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'img/Tile/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)
# bullet
bullet_img = pygame.image.load('img/icons/fireball2.1.png').convert_alpha()
# grenade
grenade_img = pygame.image.load('img/icons/momo_box.png').convert_alpha()
# pick up boxes
health_box_img = pygame.image.load('img/icons/yomari.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/momo.png').convert_alpha()
aaila_box_img = pygame.image.load('img/icons/aaila.png').convert_alpha()
item_boxes = {
    'Health': health_box_img,
    'Grenade': grenade_box_img,
    'aaila': aaila_box_img
}

# define colours
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# define font
font = pygame.font.SysFont('Futura', 30)


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def draw_bg():
    screen.fill(BG)
    scale_bg = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    width = scale_bg.get_width()
    for x in range(5):
        screen.blit(scale_bg, ((x * width) - bg_scroll, 0))


def draw_boss_health(boss_x, boss_y, health, max_health):
    ratio = health / max_health
    bar_width = 75  # Larger width for boss health bar
    bar_height = 10  # Larger height for boss health bar
    x = boss_x - bar_width // 2  # Center the bar above the boss
    y = boss_y - 40  # Position the bar above the boss's head

    pygame.draw.rect(screen, BLACK, (x - 2, y - 2, bar_width + 4, bar_height + 4))
    pygame.draw.rect(screen, RED, (x, y, bar_width, bar_height))
    pygame.draw.rect(screen, GREEN, (x, y, bar_width * ratio, bar_height))

    # Add 'BOSS' text above the health bar
    font = pygame.font.SysFont('Futura', 20)
    text = font.render('BOSS', True, RED)
    text_rect = text.get_rect(center=(boss_x, y - 15))
    screen.blit(text, text_rect)

def draw_health_bar(x, y, health, max_health):
    ratio = health / max_health
    bar_width = 40  # Adjust this value to change the width of the health bar
    bar_height = 5  # Adjust this value to change the height of the health bar
    x = x - bar_width // 2  # Center the bar above the enemy
    y = y - 20  # Position the bar above the enemy's head

    pygame.draw.rect(screen, BLACK, (x - 2, y - 2, bar_width + 4, bar_height + 4))
    pygame.draw.rect(screen, RED, (x, y, bar_width, bar_height))
    pygame.draw.rect(screen, GREEN, (x, y, bar_width * ratio, bar_height))


# function to reset level
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    # create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)

    return data


class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo, grenades, is_boss=False):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.shoot_cooldown = 0
        self.grenades = grenades
        self.health = 100
        self.max_health = self.health
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        self.is_boss = is_boss
        self.is_attacking = False

        # ai specific variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0

        # Boss-specific attributes
        if self.is_boss:
            self.health = 200
            self.max_health = 200
            scale = 1.5  # Make the boss larger

        # load all images for the players
        animation_types = ['Idle', 'Run', 'Jump', 'Death', 'punch']
        for animation in animation_types:
            # reset temporary list of images
            temp_list = []
            # count number of files in the folder
            num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
            for i in range(num_of_frames):
                img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
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
        # update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
        # reset movement variables
        screen_scroll = 0
        dx = 0
        dy = 0

        # assign movement variables if moving left or right
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        # jump
        if self.jump == True and self.in_air == False:
            self.vel_y = -11
            self.jump = False
            self.in_air = True

        # apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y
        dy += self.vel_y

        # check for collision
        for tile in world.obstacle_list:
            # check collision in x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                # if the ai has hit a wall then make it turn around
                if self.char_type == "enemy":
                    self.direction *= -1
                    self.move_counter = 0
            # check for collision in y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                # check if below the ground, i.e. jumping
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                # check if above the ground, i.e. falling
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        # check for collision with water
        if pygame.sprite.spritecollide(self, water_group, False):
            water_fx.play()
            self.health = 0

        # check for collision with exit
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        # check if fallen off the map
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

        # check if going off the edges of the screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        # update rectangle position
        self.rect.x += dx
        self.rect.y += dy

        # update scrool based on player position
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROlL_THRESH and bg_scroll < (
                    world.level_length * TILE_SIZE) - SCREEN_WIDTH) \
                    or (self.rect.left < SCROlL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx

        return screen_scroll, level_complete

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery,
                            self.direction)
            bullet_group.add(bullet)
            # reduce ammo
            self.ammo -= 1
            shot_fx.play()

    def ai(self):
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 200) == 1:
                self.update_action(0)  # 0: idle
                self.idling = True
                self.idling_counter = 50
            # check if the ai in near the player
            if self.vision.colliderect(player.rect):
                # stop running and face the player
                self.update_action(0)  # 0: idle
                # shoot
                self.shoot()
            else:
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)  # 1: run
                    self.move_counter += 1
                    # update ai vision as the enemy moves
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

            # scroll
            self.rect.x += screen_scroll

    def update_animation(self):
        # update animation
        ANIMATION_COOLDOWN = 100
        # update image depending on current frame
        self.image = self.animation_list[self.action][self.frame_index]
        # check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        # if the animation has run out the reset back to the start
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        # check if the new action is different to the previous one
        if new_action != self.action:
            self.action = new_action
            # update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)
            self.rect.x += screen_scroll

    def draw(self):
        img = pygame.transform.flip(self.image, self.flip, False)

        screen.blit(img, self.rect)

        # Draw health bar for enemies
        if self.char_type == 'enemy':
            if self.is_boss:
                # Draw only the boss health bar for the boss
                draw_boss_health(self.rect.centerx, self.rect.top, self.health, self.max_health)
            else:
                # Draw regular health bar for normal enemies
                draw_health_bar(self.rect.centerx, self.rect.top, self.health, self.max_health)


class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        # iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if 0 <= tile < len(img_list):
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if tile >= 0 and tile <= 9:
                        self.obstacle_list.append(tile_data)
                    elif tile >= 10 and tile <= 11:
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    elif tile >= 12 and tile <= 15:
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 17:  # create player
                        player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1, 5, 0, 5)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16:  # create enemies
                        enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 0.75, 2, 20, 0)
                        enemy_group.add(enemy)

                    elif tile == 18:  # create grenade box
                        item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19:  # create health box
                        item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20:  # aala
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)
                    elif tile == 21:  # create exit
                        item_box = ItemBox('aaila', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
        return player, health_bar

    def add_boss_enemy(self, x, y):
        # Create the boss enemy with max health 200
        boss_enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.5, 2, 20, 0, is_boss=True)
        enemy_group.add(boss_enemy)

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
        # scroll
        self.rect.x += screen_scroll
        # check if the player has picked up the box
        if pygame.sprite.collide_rect(self, player):
            # check what kind of box it was
            if self.item_type == 'Health':
                eat_fx.play()
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health

            elif self.item_type == 'aaila':
                drinking_fx.play()
                player.health += 100
                if player.health > player.max_health:
                    player.health = player.max_health

            elif self.item_type == 'Grenade':
                eat_fx.play()
                player.grenades += 3
            # delete the item box
            self.kill()


class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        # update with new health
        self.health = health
        # calculate health ratio
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 8
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        # move bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll
        # check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        # check for collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        # check collision with characters
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 5
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
        self.vel_y = -11
        self.speed = 7
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction

    def update(self):
        self.vel_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.vel_y

        # chekc for collision with level
        for tile in world.obstacle_list:
            # check collision with walls
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed

            # check for collision in y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0
                # check if below the ground, i.e. thrown up
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                # check if above the ground, i.e. falling
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom

        # update grenade position
        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        # countdown timer
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            grenade_fx.play()
            explosion = Explosion(self.rect.x, self.rect.y, 1.5)
            explosion_group.add(explosion)
            # do damage to anyone that is nearby
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
        for num in range(1, 6):
            img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        # scroll
        self.rect.x += screen_scroll
        EXPLOSION_SPEED = 4
        # update explosion amimation
        self.counter += 1

        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            # if the animation is complete then delete the explosion
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]


# create buttons
start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

# create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

# create empty tile list
world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)
# load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player, health_box = world.process_data(world_data)

# Position the boss enemy at the end of the level
boss_enemy_position_x = COLS - 10  # last column
boss_enemy_position_y = ROWS - 10  # adjust row as needed

world.add_boss_enemy(boss_enemy_position_x, boss_enemy_position_y)

run = True
while run:

    clock.tick(FPS)

    if start_game == False:
        # draw menu
        scale_bg = pygame.transform.scale(start_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        width = scale_bg.get_width()
        for x in range(5):
            screen.blit(scale_bg, ((x * width) - bg_scroll, 0))

        # add buttons
        if start_button.draw(screen):
            start_game = True
        if exit_button.draw(screen):
            run = False
    else:
        draw_bg()
        # draw world map
        world.draw()
        # show player health
        health_box.draw(player.health)
        draw_text('MOMO: ', font, WHITE, 10, 60)
        for x in range(player.grenades):
            screen.blit(grenade_img, (145 + (x * 40), 50))

        player.update()
        player.draw()

        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()


        # update and draw groups
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

        # update player actions
        if player.alive:
            # shoot bullets
            if shoot:
                player.shoot()
            # throw grenades
            elif grenade and grenade_thrown == False and player.grenades > 0:
                grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction), \
                                  player.rect.top, player.direction)
                grenade_group.add(grenade)
                # reduce grenades
                player.grenades -= 1
                grenade_thrown = True
            if player.in_air:
                player.update_action(2)  # 2: jump
            elif moving_left or moving_right:
                player.update_action(1)  # 1: run
            elif slash:
                player.update_action(4)  # 4: slash
            else:
                player.update_action(0)  # 0: idle
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll
            # check if player has completed the level
            if level_complete:
                level += 1
                bg_scroll = 0
                world_data = reset_level()
                if level <= MAX_LEVEL:
                    # load in level data and create world
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_box = world.process_data(world_data)

        else:
            screen_scroll = 0
            if restart_button.draw(screen):
                bg_scroll = 0
                world_data = reset_level()
                # load in level data and create world
                with open(f'level{level}_data.csv', newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)
                world = World()
                player, health_box = world.process_data(world_data)

        # handle player attack
        if slash:
            # Assuming slash is a boolean indicating whether the player is attacking
            if not player.is_attacking:  # Check if the player is not already attacking
                slash_fx.play()
                player.is_attacking = True  # Set the player's attacking state to True
                attack_offset = 50
                attack_direction = 1 if player.direction == 1 else -1
                attack_start_x = player.rect.right if player.direction == 1 else player.rect.left - attack_offset
                attacking_rect = pygame.Rect(attack_start_x, player.rect.y, attack_offset, player.rect.height)

                # List to keep track of enemies already hit during this attack
                enemies_hit = []

                for enemy in enemy_group:
                    if attacking_rect.colliderect(enemy.rect) and enemy not in enemies_hit:
                        enemy.health -= 25
                        enemies_hit.append(enemy)  # Add the enemy to the list of enemies hit during this attack

                # Play sound effect only if the player is not moving
                if moving_left == True or moving_right == True:
                    slash_fx.play()

        # At the end of the game loop or wherever appropriate, reset the attacking state
        if not slash:
            player.is_attacking = False

    walking_sound_playing = False
    # Inside the event handling loop
    for event in pygame.event.get():
        # Quit game
        if event.type == pygame.QUIT:
            run = False

        # Mouse button pressed
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Left click to attack
            if event.button == 1:  # Left mouse button

                slash = True

            # Right click to throw bomb
            if event.button == 3:  # Right mouse button
                grenade = True

        # Mouse button released
        if event.type == pygame.MOUSEBUTTONUP:
            # Left click released
            if event.button == 1:  # Left mouse button
                slash = False

            # Right click released
            if event.button == 3:  # Right mouse button
                grenade = False
                grenade_thrown = False

        # Keyboard presses
        if event.type == pygame.KEYDOWN:
            # Move left
            if event.key == pygame.K_a:
                moving_left = True
                if not walking_sound_playing or moving_right:
                    walking_fx.stop()  # Stop the currently playing sound effect
                    walking_fx.play(-1)  # Start walking sound effect from the beginning
                    walking_sound_playing = True
                    moving_right = False
            # Move right
            if event.key == pygame.K_d:
                moving_right = True
                if not walking_sound_playing or moving_left:
                    walking_fx.stop()  # Stop the currently playing sound effect
                    walking_fx.play(-1)  # Start walking sound effect from the beginning
                    walking_sound_playing = True
                    moving_left = False

        elif event.type == pygame.KEYUP:
            # Stop moving left
            if event.key == pygame.K_a:
                moving_left = False
                if not moving_right:  # If not moving right either
                    walking_fx.stop()  # Stop walking sound effect
                    walking_sound_playing = False
            # Stop moving right
            if event.key == pygame.K_d:
                moving_right = False
                if not moving_left:  # If not moving left either
                    walking_fx.stop()  # Stop walking sound effect
                    walking_sound_playing = False

            # Jump
            if event.key == pygame.K_w and player.alive:
                player.jump = True
                jump_fx.play()
            # Attack
            if event.key == pygame.K_r:
                slash = True
            # Throw bomb
            if event.key == pygame.K_q:
                grenade = True
            # Quit game
            if event.key == pygame.K_ESCAPE:
                run = False

        # Keyboard button released
        if event.type == pygame.KEYUP:
            # Stop moving left
            if event.key == pygame.K_a:
                moving_left = False
            # Stop moving right
            if event.key == pygame.K_d:
                moving_right = False
            # Stop attacking
            if event.key == pygame.K_r:
                slash = False
            # Stop throwing bomb
            if event.key == pygame.K_q:
                grenade = False
                grenade_thrown = False
            # Stop walking sound effect when player stops moving
            if not moving_left and not moving_right:
                walking_fx.stop()
                walking_sound_playing = False

    # Check if the mouse position collides with the player rect for throwing grenade
    if pygame.mouse.get_pressed()[2]:  # Right mouse button pressed
        mouse_pos = pygame.mouse.get_pos()
        if player.rect.collidepoint(mouse_pos):
            grenade = True
    else:
        grenade = False
        grenade_thrown = False

    pygame.display.update()

pygame.quit()