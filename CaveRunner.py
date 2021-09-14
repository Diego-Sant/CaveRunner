import pygame, sys, math, random

import entities as e
import core_funcs as core_funcs
import text as text

# Setup pygame/window ---------------------------------------- #
mainClock = pygame.time.Clock()
from pygame.locals import *
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.display.set_caption('Cave Runner')
screen = pygame.display.set_mode((920, 680),0,32)
pygame.mixer.set_num_channels(32)
base_screen_size = [720, 480]
display = pygame.Surface((240, 160))
pygame.mouse.set_visible(False)

def load_img(img_id):
    img = pygame.image.load('data/images/' + img_id + '.png').convert()
    img.set_colorkey((0, 0, 0))
    return img

def load_map(map_id):
    map_img = pygame.image.load('data/maps/' + map_id + '.png')
    map_data = []
    enemy_count = 0
    for y in range(map_img.get_height()):
        for x in range(map_img.get_width()):
            c = map_img.get_at((x, y))
            if c[1] == 100:
                map_data.append({'type': 'grass', 'pos': [x, y], 'h_pos': 400, 'enemy': False})
            if c[1] == 255:
                map_data.append({'type': 'bush', 'pos': [x, y], 'h_pos': 400, 'enemy': False})
            if c[2] == 100:
                map_data.append({'type': 'rocklava', 'pos': [x, y], 'h_pos': 400, 'enemy': False})
            if c[2] == 255:
                map_data.append({'type': 'box', 'pos': [x, y], 'h_pos': 400, 'enemy': False})
            if c[0] == 255:
                spawn = [x, y]
            if c[0] == 100:
                map_data[-1]['enemy'] = True
                enemy_count += 1
    return map_data, spawn, enemy_count

def advance(pos, angle, amt):
    return [pos[0] + math.cos(angle) * amt, pos[1] + math.sin(angle) * amt]

def outlined_text(bg_font, fg_font, t, surf, pos):
    bg_font.render(t, surf, [pos[0] - 1, pos[1]])
    bg_font.render(t, surf, [pos[0] + 1, pos[1]])
    bg_font.render(t, surf, [pos[0], pos[1] - 1])
    bg_font.render(t, surf, [pos[0], pos[1] + 1])
    fg_font.render(t, surf, [pos[0], pos[1]])    

e.set_global_colorkey((0, 0, 0))
e.load_animations2('data/images/animations')
e.load_particle_images('data/images/particles')

grass_tile = load_img('grass')
rock_tile = load_img('rocklava')
bush_tile = load_img('bush')
box_tile = load_img('box')
shadow_img = load_img('shadow')
shadow_img.set_alpha(150)
sword_img_raw = load_img('sword')
sword_img_covered = load_img('sword_covered')
sword_img_ground = load_img('sword_ground')
sword_img = sword_img_raw
border_img = load_img('border')
cursor_img_raw = pygame.transform.scale(load_img('cursor'), (33, 33))
cursor_img_red = pygame.transform.scale(load_img('cursor_red'), (33, 33))
cursor_img = cursor_img_raw
enemy_imgs = [load_img('enemy_0'), load_img('enemy_1')]
projectile_img = load_img('projectile')
p_shadow_img = load_img('p_shadow')
p_shadow_img.set_alpha(100)
icon_img = load_img('icon')
pygame.display.set_icon(icon_img)

jump_s = pygame.mixer.Sound('data/sfx/jump.wav')
spike_attack_s = pygame.mixer.Sound('data/sfx/spike_attack.wav')
spike_attack_hit_s = pygame.mixer.Sound('data/sfx/spike_attack_hit.wav')
destroy_enemy_s = pygame.mixer.Sound('data/sfx/destroy_enemy.wav')
hit_projectile_s = pygame.mixer.Sound('data/sfx/hit_projectile.wav')
hit_s = pygame.mixer.Sound('data/sfx/hit.wav')
land_s = pygame.mixer.Sound('data/sfx/land.wav')
spin_s = pygame.mixer.Sound('data/sfx/spin.wav')
hit_projectile_s.set_volume(0.2)
hit_s.set_volume(0.8)
land_s.set_volume(0.4)
spin_s.set_volume(0.3)
jump_s.set_volume(0.4)
spike_attack_s.set_volume(0.25)
pygame.mixer.music.load('data/music.ogg')
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.5)

main_font = text.Font('data/fonts/small_font.png', (168, 217, 227))
bg_font = text.Font('data/fonts/small_font.png', (28, 17, 24))


spin_animation = [load_img('spin/spin_' + str(i)) for i in range(23)]

falls = 0
level = 1

game_map, spawn, enemy_count = load_map('map_' + str(level - 1))
enemies_left = enemy_count
true_game_scroll = [spawn[0] * 9 - spawn[1] * 9 - display.get_width() // 2, spawn[0] * 9 + spawn[1] * 9 - display.get_height() // 2]
game_scroll = [int(true_game_scroll[0]), int(true_game_scroll[1])]

player = e.entity(spawn[0] * 100, spawn[1] * 100, 20, 20, 'player')
player.offset[1] = -21
player.offset[0] = 1
recent_collision = 0
entities = [player]

down = False
right = False

spawn_frame = 1
allow_movement = 2
player_grounded = True
last_sword_angle = 0

attack_cooldown = 0
spin_attack = 0
dash_attack = 0
spike_attack = 0
jump_cooldown = 0

display_offset = [0, 0]

projectiles = []

enemy_timer = 0
enemy_shots = 0

background_offset = 0
bar_offset = 0

sparks = []
particles = []

thanks_for_playing_pos = display.get_width() + 100

instructions_pos = display.get_width() + 300
instructions_timer = 60 * 8

while True:

    screen.fill((5, 18, 24))
    display.fill((13, 32, 43))

    instructions_timer = max(instructions_timer - 1, 0)
    if instructions_timer:
        instructions_pos += (display.get_width() // 2 - instructions_pos) / 10
    else:
        instructions_pos += (display.get_width() + 300 - instructions_pos) / 10

    background_offset = (background_offset + 0.25) % 30
    for i in range(9):
        pygame.draw.line(display, (5, 18, 24), (-10, int(i * 30 + background_offset - 20)), (display.get_width() + 10, int(i * 30 - 110 + background_offset)), 15)

#-------------------------------------------------------------------------------------

    if (enemies_left == 0) and (level < 7):
        player.h_vel = max(-12, player.h_vel - 0.11)
        if random.randint(1, 3) ==  1:
            particles.append(e.particle(player_render_x + 8, player_render_y + player.h_pos, 'p', [-0.5, 0], 0.2, 1.7, (168, 217, 227)))
            particles.append(e.particle(player_render_x + 11, player_render_y + player.h_pos, 'p', [0.5, 0], 0.2, 1.7, (168, 217, 227)))
        if player.h_pos < -800:
            player.h_pos = 1001
            falls -= 1
            level += 1
            
    if player.h_pos > 1000:
        new_level = False
        if enemies_left == 0:
            new_level = True
        player.h_pos = -250
        game_map, spawn, enemy_count = load_map('map_' + str(level - 1))
        player.set_pos((spawn[0] * 100, spawn[1] * 100))
        player_render_x = (player.x - player.y) / 100 * 9
        player_render_y = (player.x + player.y) / 100 * 9
        true_game_scroll[1] = -display.get_height() + player_render_y + player.h_pos - 50
        if new_level:
            true_game_scroll[1] += 250
        true_game_scroll[0] = -display.get_width() // 2 + player_render_x
        allow_movement = 3
        spawn_frame = 1
        enemies_left = enemy_count
        projectiles = []
        sparks = []
        particles = []
        falls += 1
        if level == 1:
            instructions_timer = 60 * 5

    for entity in entities:
        entity.rendered = False            

    mx, my = pygame.mouse.get_pos()
    true_mx = mx
    true_my = my
    mx -= (screen.get_width() - base_screen_size[0]) // 2
    my -= (screen.get_height() - base_screen_size[1]) // 2
    mx /= base_screen_size[0] / display.get_width()
    my /= base_screen_size[1] / display.get_height()

    game_mx = ((mx + game_scroll[0]) + (my + game_scroll[1])) / 18 * 100
    game_my = ((-mx - game_scroll[0]) + (my + game_scroll[1])) / 18 * 100

    player_offset_x = game_mx - 30 - player.x
    player_offset_y = game_my + 60 - player.y

    mouse_angle = math.atan2(player_offset_y, player_offset_x)

    player_speed = min(1, max(0, math.sqrt(player_offset_x ** 2 + player_offset_y ** 2) - 100) / 150)
    player_speed = player_speed ** 2
    player_speed *= 10

    player_render_x = (player.x - player.y) / 100 * 9
    player_render_y = (player.x + player.y) / 100 * 9
    true_game_scroll[0] -= (true_game_scroll[0] + display.get_width() // 2 - player_render_x) / 50
    true_game_scroll[1] -= (true_game_scroll[1] + display.get_height() // 2 - (player_render_y + player.h_pos)) / 50
    if allow_movement != 2:
        true_game_scroll[1] -= (true_game_scroll[1] + display.get_height() // 2 - (player_render_y + player.h_pos)) / 40
    if allow_movement == 3:
        true_game_scroll[1] -= (true_game_scroll[1] + display.get_height() // 2 - (player_render_y + player.h_pos)) / 20

    game_scroll = [int(true_game_scroll[0] + display_offset[0]), int(true_game_scroll[1] + display_offset[1])]        

#-------------------------------------------------------------------------------------

    tile_rects = []
    floor_rects = []
    enemies = []
    for i, tile in enumerate(game_map):
        for entity in entities:
            if not entity.rendered:
                if ((entity.x + 5) // 100 < tile['pos'][0]) and ((entity.y + 25) // 100 < tile['pos'][1] + 1):
                    if entity.type == 'player':
                        if player_grounded:
                            display.blit(shadow_img, (player_render_x - game_scroll[0] + 4, player_render_y - game_scroll[1] - 3))
                    entity.display(display, game_scroll)
                    if (entity.type == 'player') and (allow_movement < 2):
                        if player.flip:
                            e.blit_center(display, pygame.transform.rotate(pygame.transform.flip(sword_img, False, True), last_sword_angle), (player_render_x - game_scroll[0] + 7, player_render_y + player.h_pos - game_scroll[1] - 5))
                        else:
                            e.blit_center(display, pygame.transform.rotate(sword_img, last_sword_angle), (player_render_x - game_scroll[0] + 7, player_render_y + player.h_pos - game_scroll[1] - 5))
                    entity.rendered = True
                
        render_x = tile['pos'][0] * 9 - tile['pos'][1] * 9 - game_scroll[0]
        render_y = tile['pos'][0] * 9 + tile['pos'][1] * 9 - game_scroll[1]
        if (tile['h_pos'] == 400):
            if abs((player.x + 5) // 100 - tile['pos'][0]) + abs((player.y + 5) // 100 - tile['pos'][1]) < 8:
                tile['h_pos'] = 399
                if spawn_frame:
                    tile['h_pos'] = 0
            if tile['enemy']:
                if abs((player.x + 5) // 100 - tile['pos'][0]) + abs((player.y + 5) // 100 - tile['pos'][1]) < 14:
                    tile['h_pos'] = 399
        else:
            tile['h_pos'] -= tile['h_pos'] / 5
        floor_rects.append(pygame.Rect(tile['pos'][0] * 100 + 10, tile['pos'][1] * 100 - 10, 100, 100))
        if tile['type'] in ['bush', 'grass']:
            display.blit(grass_tile, (render_x, render_y + tile['h_pos']))
        if tile['type'] == 'bush':
            display.blit(bush_tile, (render_x, render_y - 9 + tile['h_pos']))
            tile_rects.append(pygame.Rect(tile['pos'][0] * 100 + 10, tile['pos'][1] * 100 - 10, 100, 100))
        if tile['type'] in ['box', 'rocklava']:
            display.blit(rock_tile, (render_x, render_y + tile['h_pos']))
        if tile['type'] == 'box':
            display.blit(box_tile, (render_x, render_y - 9 + tile['h_pos']))
            tile_rects.append(pygame.Rect(tile['pos'][0] * 100 + 10, tile['pos'][1] * 100 - 10, 100, 100))
        if tile['enemy']:
            display.blit(enemy_imgs[enemy_timer // 30], (render_x, render_y - 7 + tile['h_pos']))
            if tile['h_pos'] < 1:
                enemies.append(pygame.Rect(tile['pos'][0] * 100 + 10, tile['pos'][1] * 100 - 10, 100, 100))
            tile_rects.append(pygame.Rect(tile['pos'][0] * 100 + 10, tile['pos'][1] * 100 - 10, 100, 100))

    for entity in entities:
        if not entity.rendered:
            entity.display(display, game_scroll)
            entity.rendered = True

    if allow_movement >= 2:
        if spin_attack:
            player_speed = 0
            e.blit_center(display, spin_animation[22 - spin_attack], (player_render_x - game_scroll[0] + 7, player_render_y + player.h_pos - game_scroll[1] - 5))
        if player.flip:
            e.blit_center(display, pygame.transform.rotate(pygame.transform.flip(sword_img, False, True), last_sword_angle), (player_render_x - game_scroll[0] + 7, player_render_y + player.h_pos - game_scroll[1] - 5))
        else:
            e.blit_center(display, pygame.transform.rotate(sword_img, last_sword_angle), (player_render_x - game_scroll[0] + 7, player_render_y + player.h_pos - game_scroll[1] - 5))

#-------------------------------------------------------------------------------------

    enemy_timer += 1
    if enemy_timer > 40:
        enemy_timer = 0

    if enemy_timer == 30:
        enemy_shots += 1
        for enemy in enemies:
            for i in range(8):
                angle = math.radians(i * 45 + enemy_shots * 5)
                vel = [math.cos(angle) * 5 - abs(math.cos(angle) + math.sin(angle)), math.sin(angle) * 5 - abs(math.cos(angle) + math.sin(angle))]
                projectiles.append([[enemy.center[0] + vel[0] * 10, enemy.top + vel[1] * 10], vel, 0])

    for enemy in enemies:
        dis = math.sqrt((enemy.center[0] - player.x) ** 2 + (enemy.center[1] - player.y) ** 2)
        remove = False
        if spike_attack and (player.h_pos > -8):
            if dis < 20 / 9 * 100:
                remove = True
        if spin_attack:
            if dis < 15 / 9 * 100:
                remove = True
        if remove:
            for tile in game_map:
                if tile['pos'] == [int((enemy.x - 10) / 100), int((enemy.y + 10) / 100)]:
                    destroy_enemy_s.play()
                    enemy_colors = [(187, 37, 37), (216, 64, 251), (229, 155, 106), (244, 15, 37)]
                    for i in range(50):
                        particles.append(e.particle((enemy.x - enemy.y) / 100 * 9 + 3 + random.randint(0, 6), (enemy.x + enemy.y) / 100 * 9 + random.randint(0, 6) - 3, 'p', [random.randint(0, 8) / 4 - 1, random.randint(0, 12) / 6 - 2], 0.05, random.randint(12, 30) / 10, random.choice(enemy_colors)))
                        particles[-1].motion[1] += abs(particles[-1].motion[0]) * 0.5
                    for i in range(20):
                        sparks.append([[(enemy.x - enemy.y) / 100 * 9 + 3 + random.randint(0, 6), (enemy.x + enemy.y) / 100 * 9 + random.randint(0, 6) - 3], math.radians(random.randint(0, 359)), random.randint(4, 11), random.choice([(94, 32, 75), (239, 216, 161)])])
                    tile['enemy'] = False
                    enemies_left -= 1

#-------------------------------------------------------------------------------------

    attack_cooldown = max(0, attack_cooldown - 1)
    spin_attack = max(0, spin_attack - 1)
    dash_attack = max(0, dash_attack - 1)
    jump_cooldown = max(0, jump_cooldown - 1)

    if spike_attack == 2:
        player_speed *= 0.5

    player.velocity[0] = core_funcs.normalize(player.velocity[0], 0.7)
    player.velocity[1] = core_funcs.normalize(player.velocity[1], 0.7)    

    if jump_cooldown and (player.h_pos == 0):
        player_speed = 0

    if (player_speed == 0) or (player.h_pos != 0):
        player.set_action('idle')
        player.change_frame(1)
    else:
        player.set_action('move')
        player.change_frame(int(player_speed / 2) + 3)
    
    if (last_sword_angle >= 0) and (last_sword_angle <= 180):
        sword_img = sword_img_covered
    else:
        sword_img = sword_img_raw

    if jump_cooldown and (player.h_pos == 0):
        sword_img = sword_img_ground
        
    if (last_sword_angle >= -90) and (last_sword_angle <= 90):
        player.flip = False
    else:
        player.flip = True
        
    if allow_movement and allow_movement != 3:
        player_collisions = player.move([math.cos(mouse_angle) * player_speed + player.velocity[0], math.sin(mouse_angle) * player_speed + player.velocity[1]], tile_rects, [], [])

    if (spike_attack == 1) or (jump_cooldown):
        last_sword_angle = -90
    elif not spin_attack:
        last_sword_angle = -math.degrees(mouse_angle) - 45
    else:
        last_sword_angle = (spin_attack * 45 + 225) % 360 - 180
        if random.randint(1, 3) == 1:
            offset = math.radians(random.randint(0, 30))
            sparks.append([advance([player_render_x + 7, player_render_y - 5 + player.h_pos], math.radians(last_sword_angle) + offset, 20), math.radians(last_sword_angle) - offset, random.randint(3, 4), (239, 216, 161)])
    
    player_grounded = False
    for r in floor_rects:
        if player.obj.rect.colliderect(r):
            player_grounded = True
            break
    if allow_movement == 0:
        player_grounded = False        

    player.h_vel = min(6, player.h_vel + 0.1)
    if spike_attack == 1:
        sparks.append([[player_render_x + 6, player_render_y + 30 + player.h_pos], math.radians(random.randint(260, 280)), random.randint(5, 8), (239, 216, 161)])
        if random.randint(1, 2) == 1:
            particles.append(e.particle(player_render_x + 9, player_render_y - 2 + player.h_pos, 'p', [-0.5 + random.randint(0, 10) / 30, -2], 0.05, random.randint(30, 35) / 10, (168, 217, 227)))
            particles.append(e.particle(player_render_x + 11, player_render_y - 2 + player.h_pos, 'p', [0.5 - random.randint(0, 10) / 30, -2], 0.05, random.randint(30, 35) / 10, (168, 217, 227)))
    if (spike_attack == 2) and (player.h_vel > 0):
        spike_attack = 1
        player.h_vel = 7
        spike_attack_s.play()
        for i in range(20):
            sparks.append([[player_render_x + 6, player_render_y + 50 + player.h_pos], math.radians(random.randint(260, 280)), random.randint(8, 12), (239, 216, 161)])
    if not player_grounded:
        player.h_pos += player.h_vel
        if player.h_pos > 0:
            if allow_movement == 2:
                allow_movement = 1
    else:
        player.h_pos += player.h_vel
        if player.h_pos > 0:
            if player.h_vel > 2:
                land_s.play()
                particles.append(e.particle(player_render_x + 9, player_render_y - 2 + player.h_pos, 'p', [-0.7, 0], 0.4, 1.7, (168, 217, 227)))
                particles.append(e.particle(player_render_x + 10, player_render_y + player.h_pos, 'p', [-0.25, 0], 0.25, 1.7, (168, 217, 227)))
                particles.append(e.particle(player_render_x + 10, player_render_y + player.h_pos, 'p', [0.25, 0], 0.25, 1.7, (168, 217, 227)))
                particles.append(e.particle(player_render_x + 11, player_render_y - 2 + player.h_pos, 'p', [0.7, 0], 0.4, 1.7, (168, 217, 227)))
            if spike_attack == 1:
                spike_attack_hit_s.play()
                spike_attack = 0
                player.velocity = [0, 0]
                for i in range(10):
                    sparks.append([[player_render_x + 7, player_render_y + 14], math.radians(random.randint(180, 360)), random.randint(6, 10)])
                for i in range(12):
                    particles.append(e.particle(player_render_x + 9, player_render_y + 3 + player.h_pos, 'p', [random.randint(0, 20) / 20 - 0.5, random.randint(0, 20) / 20 - 1], 0.15, random.randint(15, 25) / 10, (168, 217, 227)))
            if allow_movement == 1:
                allow_movement = 0
            else:
                if allow_movement == 3:
                    allow_movement = 2
                player.h_pos = 0
                player.h_vel = 0

#-------------------------------------------------------------------------------------

    for i, particle in sorted(enumerate(particles), reverse=True):
        alive = particle.update(1)
        particle.motion[1] += 0.05
        if not alive:
            particles.pop(i)
        else:
            particle.draw(display, game_scroll)

    for i, spark in sorted(enumerate(sparks), reverse=True):
        spark[1] = spark[1] % (math.pi * 2)
        # pos, angle, speed
        spark[0] = advance(spark[0], spark[1], spark[2])
        
        spark_points = [
            advance(spark[0], spark[1], spark[2] * 3),
            advance(spark[0], spark[1] + math.radians(90), spark[2] * 0.25),
            advance(spark[0], spark[1], spark[2] * -1.2),
            advance(spark[0], spark[1] + math.radians(-90), spark[2] * 0.25),
            ]

        if len(spark) != 5:
            if (math.degrees(spark[1]) > 90) and (math.degrees(spark[1]) < 270):
                spark[1] -= math.radians(3)
            else:
                spark[1] += math.radians(3)

        spark_points = [[p[0] - game_scroll[0], p[1] - game_scroll[1]] for p in spark_points]

        if len(spark) == 3:
            pygame.draw.polygon(display, (168, 217, 227), spark_points)
        else:
            pygame.draw.polygon(display, spark[3], spark_points)
        
        spark[2] -= 0.3
        if spark[2] < 0:
            sparks.pop(i)

#-------------------------------------------------------------------------------------

    for projectile in projectiles:
        projectile[0][0] += projectile[1][0]
        projectile[0][1] += projectile[1][1]
        render_x = (projectile[0][0] - projectile[0][1]) / 100 * 9
        render_y = (projectile[0][0] + projectile[0][1]) / 100 * 9
        try:
            if display.get_at((int(render_x - game_scroll[0]), int(render_y + 8 - game_scroll[1])))[0] != 13:
                display.blit(p_shadow_img, (render_x - game_scroll[0], render_y + 8 - game_scroll[1]))
        except IndexError:
            pass
    for i, projectile in sorted(enumerate(projectiles), reverse=True):
        render_x = (projectile[0][0] - projectile[0][1]) / 100 * 9
        render_y = (projectile[0][0] + projectile[0][1]) / 100 * 9
        dis = math.sqrt((render_x - player_render_x - 7) ** 2 + (render_y - player_render_y + 7) ** 2)
        if spin_attack or (spike_attack and (player.h_pos > -8)):
            if dis < 35:
                if not projectile[2]:
                    hit_projectile_s.play()
                    angle = math.atan2(player_render_y - 7 - render_y, player_render_x + 7 - render_x)
                    angle += math.pi
                    projectile[1] = [math.cos(angle) * 20, math.sin(angle) * 20]
                    projectile[2] = 1
                    for i in range(4):
                        sparks.append([[render_x, render_y], angle, random.randint(3, 5)])
        elif (player.h_pos > -4) and dis < 30:
            head_dis = math.sqrt((render_x - player_render_x - 7) ** 2 + (render_y - player_render_y + 12) ** 2)
            if dis < 12:
                angle = math.atan2(player_render_y - 7 - render_y, player_render_x + 7 - render_x)
                if not projectile[2]:
                    for i in range(4):
                        sparks.append([[render_x, render_y], math.radians(random.randint(0, 359)), random.randint(3, 4)])
                    force_reduction = 20 / (abs(player.velocity[0]) + abs(player.velocity[1]) + 20)
                    hit_s.play()
                    player.velocity[0] += math.cos(angle) * 12 * force_reduction
                    player.velocity[1] += math.sin(angle) * 12 * force_reduction
                    angle += math.pi
                    projectile[1] = [math.cos(angle) * 20, math.sin(angle) * 20]
                    projectile[2] = 1
        if dis > 300:
            projectiles.pop(i)
        display.blit(projectile_img, (render_x - game_scroll[0], render_y - game_scroll[1]))

#-------------------------------------------------------------------------------------

    if player_speed >= 8:
        bar_offset += (15 - bar_offset) / 20
        cursor_img = cursor_img_red
    else:
        bar_offset += (-bar_offset) / 50
        cursor_img = cursor_img_raw
        
    pygame.draw.rect(display, (5, 18, 24), pygame.Rect(0, display.get_height() - bar_offset, display.get_width(), 15))
    pygame.draw.rect(display, (5, 18, 24), pygame.Rect(0, -15 + bar_offset, display.get_width(), 15))
    outlined_text(bg_font, main_font, 'Level - ' + str(level), display, (8, 5))
    outlined_text(bg_font, main_font, str(enemy_count - enemies_left) + '/' + str(enemy_count), display, (8, 15))

    outlined_text(bg_font, main_font, 'Mouse Esquerdo: Atacar', display, (instructions_pos - main_font.width('Mouse Esquerdo: Atacar') // 2, 110))
    outlined_text(bg_font, main_font, 'Mouse Direito: Pular', display, (instructions_pos - main_font.width('Mouse Direito: Pular') // 2, 120))
    outlined_text(bg_font, main_font, 'Destrua:', display, (instructions_pos - main_font.width('Destrua:') // 2, 15))
    e.blit_center(display, enemy_imgs[enemy_timer // 30], (instructions_pos, 35))

    if level == 7:
        if allow_movement == 2:
            thanks_for_playing_pos += ((display.get_width() // 2 - main_font.width('Obrigado por jogar!') // 2) - thanks_for_playing_pos) / 10

        bg_font.render('Obrigado por jogar!', display, (thanks_for_playing_pos - 1, display.get_height() // 3))
        bg_font.render('Obrigado por jogar!', display, (thanks_for_playing_pos + 1, display.get_height() // 3))
        bg_font.render('Obrigado por jogar!', display, (thanks_for_playing_pos, display.get_height() // 3 - 1))
        bg_font.render('Obrigado por jogar!', display, (thanks_for_playing_pos, display.get_height() // 3 + 1))
        main_font.render('Obrigado por jogar!', display, (thanks_for_playing_pos, display.get_height() // 3))

#-------------------------------------------------------------------------------------

    for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 3:
                    if (player.h_pos < 3) and (player.h_pos >= 0) and (jump_cooldown == 0):
                        player.h_vel = -2.5
                        jump_s.play()
                        allow_movement = 2
                        particles.append(e.particle(player_render_x + 8, player_render_y - 2, 'p', [-0.5, 0], 0.2, 1.7, (168, 217, 227)))
                        particles.append(e.particle(player_render_x + 10, player_render_y - 2, 'p', [0.5, 0], 0.2, 1.7, (168, 217, 227)))
                if event.button == 1:
                    if attack_cooldown == 0:
                        if player.h_pos == 0:
                            spin_s.play()
                            if player_speed < 8:
                                attack_cooldown = 22
                                spin_attack = 22
                            else:
                                player.velocity[0] += math.cos(mouse_angle) * 30
                                player.velocity[1] += math.sin(mouse_angle) * 30
                                dash_attack = 20
                                spin_attack = 22
                                attack_cooldown = 45
                                for i in range(7):
                                    sparks.append([[player_render_x + 7, player_render_y - 5 + player.h_pos], math.radians(math.degrees(mouse_angle) + 225 + random.randint(0, 60) - 30), random.randint(3, 9), (239, 216, 161), 1])
                        elif player.h_pos < 0:
                            attack_cooldown = 120
                            player.h_vel = -4
                            jump_s.play()
                            spike_attack = 2
                            jump_cooldown = 120
                            particles.append(e.particle(player_render_x + 8, player_render_y - 2 + player.h_pos, 'p', [-0.5, 0], 0.2, 1.7, (168, 217, 227)))
                            particles.append(e.particle(player_render_x + 9, player_render_y - 2 + player.h_pos, 'p', [-0.25, 0], 0.2, 1.7, (168, 217, 227)))
                            particles.append(e.particle(player_render_x + 9, player_render_y - 2 + player.h_pos, 'p', [0.25, 0], 0.2, 1.7, (168, 217, 227)))
                            particles.append(e.particle(player_render_x + 10, player_render_y - 2 + player.h_pos, 'p', [0.5, 0], 0.2, 1.7, (168, 217, 227)))
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == K_e:
                    player.move([1, 0], [], [], [])
                if event.key == K_q:
                    player.move([0, 1], [], [], [])
                if event.key == K_s:
                    down = True
                if event.key == K_d:
                    right = True
            if event.type == KEYUP:
                if event.key == K_s:
                    down = False
                if event.key == K_d:
                    right = False    


#-------------------------------------------------------------------------------------                

    spawn_frame = 0
    screen.blit(pygame.transform.scale(display, base_screen_size), ((screen.get_width() - base_screen_size[0]) // 2, (screen.get_height() - base_screen_size[1]) // 2))
    screen.blit(pygame.transform.scale(border_img, base_screen_size), ((screen.get_width() - base_screen_size[0]) // 2, (screen.get_height() - base_screen_size[1]) // 2 + bar_offset * 3))
    screen.blit(pygame.transform.scale(border_img, base_screen_size), ((screen.get_width() - base_screen_size[0]) // 2, (screen.get_height() - base_screen_size[1]) // 2 - bar_offset * 3))
    screen.blit(cursor_img, (true_mx // 3 * 3 + 1, true_my // 3 * 3 + 1))
    pygame.display.update()
    mainClock.tick(60)