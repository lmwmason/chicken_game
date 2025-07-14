import sys
import pygame
from pygame.locals import *
import os
import random
import math

folder = os.getcwd()
pygame.init()

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
GameDisplay = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Epic Chicken Adventure - Ultimate Edition")

FPS = 60
FramePerSec = pygame.time.Clock()

BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)
GRAY = (128, 128, 128)
CYAN = (0, 255, 255)
LIME = (50, 205, 50)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)

font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
big_font = pygame.font.Font(None, 72)
huge_font = pygame.font.Font(None, 96)

game_state = "playing"
score = 0
level = 1
time_survived = 0
high_score = 0
combo = 0
max_combo = 0
screen_shake = 0
boss_mode = False
boss_health = 100
boss_max_health = 100

POWER_SPEED = "speed"
POWER_SHIELD = "shield"
POWER_MAGNET = "magnet"
POWER_FREEZE = "freeze"
POWER_LIGHTNING = "lightning"
POWER_MULTIPLY = "multiply"
POWER_GIANT = "giant"
POWER_INVISIBLE = "invisible"


class ScreenShake:
    def __init__(self):
        self.amount = 0
        self.duration = 0

    def add_shake(self, amount, duration):
        self.amount = max(self.amount, amount)
        self.duration = max(self.duration, duration)

    def update(self):
        if self.duration > 0:
            self.duration -= 1
            if self.duration == 0:
                self.amount = 0

    def get_offset(self):
        if self.amount > 0:
            return (random.randint(-self.amount, self.amount), random.randint(-self.amount, self.amount))
        return (0, 0)


shake_manager = ScreenShake()


class FloatingText:
    def __init__(self, x, y, text, color, size=24):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.font = pygame.font.Font(None, size)
        self.life = 120
        self.max_life = 120
        self.vy = -2

    def update(self):
        self.y += self.vy
        self.life -= 1
        self.vy *= 0.98

    def draw(self, surface):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            text_surface = self.font.render(self.text, True, self.color)
            text_surface.set_alpha(alpha)
            surface.blit(text_surface, (self.x, self.y))


class Lightning:
    def __init__(self, x, y, target_x, target_y):
        self.start_x = x
        self.start_y = y
        self.end_x = target_x
        self.end_y = target_y
        self.segments = []
        self.life = 30
        self.generate_segments()

    def generate_segments(self):
        points = [(self.start_x, self.start_y)]
        dx = self.end_x - self.start_x
        dy = self.end_y - self.start_y

        for i in range(1, 8):
            progress = i / 8
            x = self.start_x + dx * progress + random.randint(-20, 20)
            y = self.start_y + dy * progress + random.randint(-20, 20)
            points.append((x, y))

        points.append((self.end_x, self.end_y))
        self.segments = points

    def update(self):
        self.life -= 1
        if self.life % 3 == 0:
            self.generate_segments()

    def draw(self, surface):
        if self.life > 0:
            for i in range(len(self.segments) - 1):
                pygame.draw.line(surface, CYAN, self.segments[i], self.segments[i + 1], 3)
                pygame.draw.line(surface, WHITE, self.segments[i], self.segments[i + 1], 1)


class Explosion:
    def __init__(self, x, y, size=50):
        self.x = x
        self.y = y
        self.size = size
        self.max_size = size
        self.life = 30
        self.max_life = 30
        self.particles = []
        for _ in range(20):
            self.particles.append({
                'x': x + random.randint(-10, 10),
                'y': y + random.randint(-10, 10),
                'vx': random.uniform(-5, 5),
                'vy': random.uniform(-5, 5),
                'color': random.choice([RED, ORANGE, YELLOW, WHITE])
            })

    def update(self):
        self.life -= 1
        self.size = self.max_size * (self.life / self.max_life)

        for particle in self.particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vx'] *= 0.95
            particle['vy'] *= 0.95

    def draw(self, surface):
        if self.life > 0:
            for particle in self.particles:
                alpha = int(255 * (self.life / self.max_life))
                pygame.draw.circle(surface, particle['color'],
                                   (int(particle['x']), int(particle['y'])),
                                   max(1, int(self.size / 10)))


class Particle:
    def __init__(self, x, y, color, size=3, life=30):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.gravity = 0.1

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= 1
        self.size = max(1, self.size * (self.life / self.max_life))

    def draw(self, surface):
        if self.life > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))


class Character:
    def __init__(self):
        try:
            self.original_image = pygame.image.load(folder + '\\img\\chicken.png')
            self.original_image = pygame.transform.flip(self.original_image, True, False)
            self.original_image = pygame.transform.scale(self.original_image, (80, 60))
        except:
            self.original_image = pygame.Surface((80, 60))
            self.original_image.fill(YELLOW)
            pygame.draw.circle(self.original_image, ORANGE, (20, 20), 15)
            pygame.draw.circle(self.original_image, RED, (15, 15), 3)

        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.speed = 6
        self.base_speed = 6
        self.angle = 0
        self.size_multiplier = 1.0
        self.base_size = (80, 60)

        self.power_ups = {}
        self.power_timers = {}
        self.shield_active = False
        self.magnet_active = False
        self.speed_boost = False
        self.invisible = False
        self.giant = False

        self.trail = []
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.dash_cooldown = 0
        self.dash_distance = 100

    def update(self):
        for power in list(self.power_timers.keys()):
            self.power_timers[power] -= 1
            if self.power_timers[power] <= 0:
                self.deactivate_power(power)

        if self.invulnerable:
            self.invulnerable_timer -= 1
            if self.invulnerable_timer <= 0:
                self.invulnerable = False

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 15:
            self.trail.pop(0)

        new_size = (int(self.base_size[0] * self.size_multiplier),
                    int(self.base_size[1] * self.size_multiplier))

        if abs(self.angle) > 1:
            scaled_image = pygame.transform.scale(self.original_image, new_size)
            self.image = pygame.transform.rotate(scaled_image, self.angle)
            old_center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = old_center
        else:
            self.image = pygame.transform.scale(self.original_image, new_size)
            old_center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = old_center

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

        if self.rect.x < 0:
            self.rect.x = 0
        elif self.rect.x > SCREEN_WIDTH - self.rect.width:
            self.rect.x = SCREEN_WIDTH - self.rect.width
        if self.rect.y < 0:
            self.rect.y = 0
        elif self.rect.y > SCREEN_HEIGHT - self.rect.height:
            self.rect.y = SCREEN_HEIGHT - self.rect.height

        if dx != 0 or dy != 0:
            self.angle = math.degrees(math.atan2(-dy, dx))

    def dash(self, dx, dy):
        if self.dash_cooldown == 0:
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                dx = dx / length * self.dash_distance
                dy = dy / length * self.dash_distance
                self.move(dx, dy)
                self.dash_cooldown = 60
                self.invulnerable = True
                self.invulnerable_timer = 10
                shake_manager.add_shake(5, 10)
                return True
        return False

    def activate_power(self, power_type):
        if power_type == POWER_SPEED:
            self.speed = self.base_speed * 2
            self.speed_boost = True
            self.power_timers[power_type] = 400
        elif power_type == POWER_SHIELD:
            self.shield_active = True
            self.power_timers[power_type] = 800
        elif power_type == POWER_MAGNET:
            self.magnet_active = True
            self.power_timers[power_type] = 600
        elif power_type == POWER_FREEZE:
            self.power_timers[power_type] = 240
        elif power_type == POWER_LIGHTNING:
            self.power_timers[power_type] = 300
        elif power_type == POWER_MULTIPLY:
            self.power_timers[power_type] = 1
        elif power_type == POWER_GIANT:
            self.size_multiplier = 2.0
            self.giant = True
            self.power_timers[power_type] = 480
        elif power_type == POWER_INVISIBLE:
            self.invisible = True
            self.power_timers[power_type] = 360

    def deactivate_power(self, power_type):
        if power_type == POWER_SPEED:
            self.speed = self.base_speed
            self.speed_boost = False
        elif power_type == POWER_SHIELD:
            self.shield_active = False
        elif power_type == POWER_MAGNET:
            self.magnet_active = False
        elif power_type == POWER_GIANT:
            self.size_multiplier = 1.0
            self.giant = False
        elif power_type == POWER_INVISIBLE:
            self.invisible = False

        if power_type in self.power_timers:
            del self.power_timers[power_type]

    def draw(self, surface):
        if len(self.trail) > 1:
            for i, pos in enumerate(self.trail):
                alpha = int(255 * (i / len(self.trail)))
                trail_color = CYAN if self.speed_boost else WHITE
                size = max(1, int(i * self.size_multiplier))
                pygame.draw.circle(surface, trail_color, pos, size)

        if not self.invulnerable or pygame.time.get_ticks() % 100 < 50:
            if not self.invisible or pygame.time.get_ticks() % 200 < 100:
                surface.blit(self.image, self.rect)

        if self.shield_active:
            shield_radius = int(60 * self.size_multiplier)
            pygame.draw.circle(surface, BLUE, self.rect.center, shield_radius, 4)
            pygame.draw.circle(surface, CYAN, self.rect.center, shield_radius + 5, 2)

        if self.magnet_active:
            magnet_radius = int(80 * self.size_multiplier)
            pygame.draw.circle(surface, PURPLE, self.rect.center, magnet_radius, 3)

        if self.dash_cooldown > 0:
            cooldown_bar_width = 60
            cooldown_progress = (60 - self.dash_cooldown) / 60
            pygame.draw.rect(surface, RED, (self.rect.x, self.rect.y - 10, cooldown_bar_width, 5))
            pygame.draw.rect(surface, GREEN, (self.rect.x, self.rect.y - 10, cooldown_bar_width * cooldown_progress, 5))


class Boss:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = boss_max_health
        self.max_health = boss_max_health
        self.speed = 2
        self.size = 100
        self.color = RED
        self.attack_timer = 0
        self.pattern = 0
        self.pattern_timer = 0
        self.angle = 0
        self.spawn_timer = 0

    def update(self, target_x, target_y):
        self.pattern_timer += 1

        if self.pattern_timer > 300:
            self.pattern = (self.pattern + 1) % 3
            self.pattern_timer = 0

        if self.pattern == 0:
            dx = target_x - self.x
            dy = target_y - self.y
            dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
            self.x += self.speed * dx / dist
            self.y += self.speed * dy / dist
        elif self.pattern == 1:
            self.angle += 0.05
            self.x += math.cos(self.angle) * 3
            self.y += math.sin(self.angle) * 3
        elif self.pattern == 2:
            self.spawn_timer += 1
            if self.spawn_timer > 60:
                self.spawn_timer = 0
                return "spawn_minion"

        self.x = max(50, min(SCREEN_WIDTH - 50, self.x))
        self.y = max(50, min(SCREEN_HEIGHT - 50, self.y))

        return None

    def take_damage(self, damage):
        self.health -= damage
        shake_manager.add_shake(8, 15)
        return self.health <= 0

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(surface, BLACK, (int(self.x - 20), int(self.y - 20)), 8)
        pygame.draw.circle(surface, BLACK, (int(self.x + 20), int(self.y - 20)), 8)

        health_bar_width = 200
        health_progress = self.health / self.max_health
        pygame.draw.rect(surface, RED, (self.x - 100, self.y - 150, health_bar_width, 20))
        pygame.draw.rect(surface, GREEN, (self.x - 100, self.y - 150, health_bar_width * health_progress, 20))


class Follower:
    def __init__(self, x, y, speed, color, size=50, follower_type="normal"):
        self.x = x
        self.y = y
        self.speed = speed
        self.base_speed = speed
        self.color = color
        self.size = size
        self.frozen = False
        self.frozen_timer = 0
        self.angle = 0
        self.wobble = 0
        self.type = follower_type
        self.health = 1 if follower_type == "normal" else 3
        self.max_health = self.health

        try:
            self.image = pygame.image.load(folder + f'\\img\\follower{random.randint(1, 2)}.png')
            self.image = pygame.transform.scale(self.image, (size, size))
        except:
            self.image = pygame.Surface((size, size))
            self.image.fill(color)
            if follower_type == "tank":
                pygame.draw.rect(self.image, GRAY, (0, 0, size, size), 5)
            elif follower_type == "fast":
                pygame.draw.circle(self.image, YELLOW, (size // 2, size // 2), 3)
            pygame.draw.circle(self.image, BLACK, (size // 4, size // 4), 3)
            pygame.draw.circle(self.image, BLACK, (3 * size // 4, size // 4), 3)

    def update(self, target_x, target_y):
        if self.frozen:
            self.frozen_timer -= 1
            if self.frozen_timer <= 0:
                self.frozen = False
            return

        dx = target_x - self.x
        dy = target_y - self.y
        dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)

        if dist > 1:
            move_speed = self.speed
            if self.type == "fast":
                move_speed *= 1.5
            elif self.type == "tank":
                move_speed *= 0.7

            self.x += move_speed * dx / dist
            self.y += move_speed * dy / dist

        self.wobble += 0.2
        self.angle = math.sin(self.wobble) * 10

    def freeze(self, duration):
        self.frozen = True
        self.frozen_timer = duration

    def take_damage(self, damage=1):
        self.health -= damage
        return self.health <= 0

    def draw(self, surface):
        if self.frozen:
            ice_surface = pygame.Surface((self.size + 10, self.size + 10))
            ice_surface.set_alpha(150)
            ice_surface.fill(BLUE)
            surface.blit(ice_surface, (self.x - 5, self.y - 5))

        if abs(self.angle) > 1:
            rotated = pygame.transform.rotate(self.image, self.angle)
            rect = rotated.get_rect(center=(self.x + self.size // 2, self.y + self.size // 2))
            surface.blit(rotated, rect)
        else:
            surface.blit(self.image, (self.x, self.y))

        if self.type == "tank" and self.health < self.max_health:
            health_width = 40
            health_progress = self.health / self.max_health
            pygame.draw.rect(surface, RED, (self.x, self.y - 10, health_width, 5))
            pygame.draw.rect(surface, GREEN, (self.x, self.y - 10, health_width * health_progress, 5))


class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.power_type = power_type
        self.size = 25
        self.collected = False
        self.pulse = 0
        self.rotation = 0

        colors = {
            POWER_SPEED: GREEN,
            POWER_SHIELD: BLUE,
            POWER_MAGNET: PURPLE,
            POWER_FREEZE: CYAN,
            POWER_LIGHTNING: YELLOW,
            POWER_MULTIPLY: GOLD,
            POWER_GIANT: RED,
            POWER_INVISIBLE: GRAY
        }
        self.color = colors[power_type]

    def update(self, character):
        self.pulse += 0.3
        self.rotation += 2

        if character.magnet_active:
            dx = character.rect.centerx - self.x
            dy = character.rect.centery - self.y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist < 150:
                self.x += dx * 0.15
                self.y += dy * 0.15

        collision_radius = 35 if character.giant else 30
        if (abs(self.x - character.rect.centerx) < collision_radius and
                abs(self.y - character.rect.centery) < collision_radius):
            self.collected = True
            return True
        return False

    def draw(self, surface):
        if not self.collected:
            size = self.size + int(math.sin(self.pulse) * 8)

            points = []
            for i in range(6):
                angle = math.radians(i * 60 + self.rotation)
                x = self.x + math.cos(angle) * size
                y = self.y + math.sin(angle) * size
                points.append((x, y))

            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, WHITE, points, 3)

            text = small_font.render(self.power_type[:3].upper(), True, BLACK)
            text_rect = text.get_rect(center=(self.x, self.y))
            surface.blit(text, text_rect)


class Coin:
    def __init__(self, x, y, coin_type="normal"):
        self.x = x
        self.y = y
        self.collected = False
        self.spin = 0
        self.type = coin_type
        self.bounce = 0

        if coin_type == "gold":
            self.value = 50
            self.color = GOLD
        elif coin_type == "silver":
            self.value = 25
            self.color = SILVER
        else:
            self.value = 10
            self.color = YELLOW

    def update(self, character):
        self.spin += 0.7
        self.bounce += 0.4

        magnet_range = 150 if character.magnet_active else 0
        if character.magnet_active:
            dx = character.rect.centerx - self.x
            dy = character.rect.centery - self.y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist < magnet_range:
                self.x += dx * 0.2
                self.y += dy * 0.2

        collision_radius = 35 if character.giant else 25
        if (abs(self.x - character.rect.centerx) < collision_radius and
                abs(self.y - character.rect.centery) < collision_radius):
            self.collected = True
            return True
        return False

    def draw(self, surface):
        if not self.collected:
            scale = abs(math.sin(self.spin))
            width = int(25 * scale) + 8
            y_offset = int(math.sin(self.bounce) * 3)

            pygame.draw.ellipse(surface, self.color,
                                (self.x - width // 2, self.y - 12 + y_offset, width, 24))
            pygame.draw.ellipse(surface, WHITE,
                                (self.x - width // 2, self.y - 12 + y_offset, width, 24), 2)

            if self.type != "normal":
                star_size = 8
                points = []
                for i in range(5):
                    angle = math.radians(i * 72 + self.spin * 10)
                    x = self.x + math.cos(angle) * star_size
                    y = self.y + math.sin(angle) * star_size + y_offset
                    points.append((x, y))
                pygame.draw.polygon(surface, WHITE, points)


character = Character()
followers = []
coins = []
power_ups = []
particles = []
explosions = []
floating_texts = []
lightning_bolts = []
boss = None

for i in range(5):
    follower_type = random.choice(["normal", "normal", "normal", "fast", "tank"])
    followers.append(Follower(
        random.randint(0, SCREEN_WIDTH - 50),
        random.randint(0, SCREEN_HEIGHT - 50),
        random.randint(2, 4),
        random.choice([RED, GREEN, BLUE, PURPLE, ORANGE]),
        50,
        follower_type
    ))

spawn_timer = 0
powerup_timer = 0
coin_timer = 0
combo_timer = 0

clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(FPS)
    shake_manager.update()
    shake_offset = shake_manager.get_offset()

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_SPACE:
                if game_state == "game_over":
                    game_state = "playing"
                    score = 0
                    level = 1
                    time_survived = 0
                    combo = 0
                    max_combo = 0
                    boss_mode = False
                    character = Character()
                    followers = []
                    coins = []
                    power_ups = []
                    particles = []
                    explosions = []
                    floating_texts = []
                    lightning_bolts = []
                    boss = None
                    for i in range(5):
                        follower_type = random.choice(["normal", "normal", "normal", "fast", "tank"])
                        followers.append(Follower(
                            random.randint(0, SCREEN_WIDTH - 50),
                            random.randint(0, SCREEN_HEIGHT - 50),
                            random.randint(2, 4),
                            random.choice([RED, GREEN, BLUE, PURPLE, ORANGE]),
                            50,
                            follower_type
                        ))
                else:
                    keys = pygame.key.get_pressed()
                    dx = dy = 0
                    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                        dx = -1
                    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                        dx = 1
                    if keys[pygame.K_UP] or keys[pygame.K_w]:
                        dy = -1
                    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                        dy = 1

                    if character.dash(dx * character.speed, dy * character.speed):
                        for _ in range(10):
                            particles.append(Particle(
                                character.rect.centerx + random.randint(-20, 20),
                                character.rect.centery + random.randint(-20, 20),
                                CYAN, 4, 40
                            ))

    if game_state == "playing":
        time_survived += 1
        if time_survived % 600 == 0:
            level += 1
            floating_texts.append(FloatingText(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                f"LEVEL {level}!", GOLD, 48
            ))
            shake_manager.add_shake(10, 30)

        if level >= 10 and not boss_mode and time_survived % 1800 == 0:
            boss_mode = True
            boss = Boss(SCREEN_WIDTH // 2, 100)
            boss_health = boss_max_health
            floating_texts.append(FloatingText(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                "BOSS FIGHT!", RED, 72
            ))
            shake_manager.add_shake(15, 60)

        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -character.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = character.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -character.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = character.speed

        character.move(dx, dy)
        character.update()

        if combo_timer > 0:
            combo_timer -= 1
        else:
            combo = 0

        if boss_mode and boss:
            boss_action = boss.update(character.rect.centerx, character.rect.centery)
            if boss_action == "spawn_minion":
                followers.append(Follower(
                    boss.x + random.randint(-50, 50),
                    boss.y + random.randint(-50, 50),
                    random.randint(3, 5),
                    RED,
                    40,
                    "fast"
                ))

            if (abs(boss.x - character.rect.centerx) < 80 and
                    abs(boss.y - character.rect.centery) < 80):
                if character.shield_active:
                    character.shield_active = False
                    character.power_timers[POWER_SHIELD] = 0
                    boss.take_damage(20)
                    explosions.append(Explosion(boss.x, boss.y, 80))
                    floating_texts.append(FloatingText(boss.x, boss.y - 50, "SHIELD HIT!", BLUE, 36))
                elif not character.invulnerable:
                    if character.giant:
                        boss.take_damage(30)
                        explosions.append(Explosion(boss.x, boss.y, 100))
                        floating_texts.append(FloatingText(boss.x, boss.y - 50, "GIANT SMASH!", RED, 48))
                        character.invulnerable = True
                        character.invulnerable_timer = 60
                    else:
                        game_state = "game_over"
                        if score > high_score:
                            high_score = score

            if boss.health <= 0:
                boss_mode = False
                score += 1000
                combo += 50
                max_combo = max(max_combo, combo)
                floating_texts.append(FloatingText(boss.x, boss.y, "BOSS DEFEATED! +1000", GOLD, 48))
                explosions.append(Explosion(boss.x, boss.y, 150))
                shake_manager.add_shake(20, 60)
                for _ in range(50):
                    particles.append(Particle(
                        boss.x + random.randint(-100, 100),
                        boss.y + random.randint(-100, 100),
                        random.choice([GOLD, YELLOW, ORANGE, RED]),
                        random.randint(3, 8),
                        60
                    ))
                for _ in range(10):
                    coin_type = random.choice(["gold", "gold", "silver", "normal"])
                    coins.append(Coin(
                        boss.x + random.randint(-100, 100),
                        boss.y + random.randint(-100, 100),
                        coin_type
                    ))
                boss = None

        freeze_active = POWER_FREEZE in character.power_timers
        lightning_active = POWER_LIGHTNING in character.power_timers

        for follower in followers[:]:
            if freeze_active and not follower.frozen:
                follower.freeze(120)

            follower.update(character.rect.centerx, character.rect.centery)

            if lightning_active and random.randint(1, 30) == 1:
                lightning_bolts.append(Lightning(
                    character.rect.centerx, character.rect.centery,
                    follower.x + follower.size // 2, follower.y + follower.size // 2
                ))
                if follower.take_damage(1):
                    followers.remove(follower)
                    score += 20
                    combo += 1
                    max_combo = max(max_combo, combo)
                    combo_timer = 120
                    floating_texts.append(FloatingText(
                        follower.x, follower.y, f"ZAP! +20 x{combo}", CYAN, 24
                    ))
                    explosions.append(Explosion(follower.x, follower.y, 40))
                    for _ in range(8):
                        particles.append(Particle(
                            follower.x + random.randint(-20, 20),
                            follower.y + random.randint(-20, 20),
                            CYAN, 3, 30
                        ))
                continue

            collision_margin = 60 if character.giant else 40
            if (abs(follower.x - character.rect.x) < collision_margin and
                    abs(follower.y - character.rect.y) < collision_margin):
                if character.shield_active:
                    character.shield_active = False
                    character.power_timers[POWER_SHIELD] = 0
                    if follower.take_damage(2):
                        followers.remove(follower)
                        score += 30
                        combo += 1
                        max_combo = max(max_combo, combo)
                        combo_timer = 120
                        floating_texts.append(FloatingText(
                            follower.x, follower.y, f"SHIELD! +30 x{combo}", BLUE, 28
                        ))
                    explosions.append(Explosion(follower.x, follower.y, 60))
                    for _ in range(12):
                        particles.append(Particle(
                            follower.x + random.randint(-30, 30),
                            follower.y + random.randint(-30, 30),
                            BLUE, 4, 40
                        ))
                elif character.giant:
                    if follower.take_damage(3):
                        followers.remove(follower)
                        score += 40
                        combo += 1
                        max_combo = max(max_combo, combo)
                        combo_timer = 120
                        floating_texts.append(FloatingText(
                            follower.x, follower.y, f"GIANT! +40 x{combo}", RED, 32
                        ))
                    explosions.append(Explosion(follower.x, follower.y, 80))
                    shake_manager.add_shake(8, 20)
                    for _ in range(15):
                        particles.append(Particle(
                            follower.x + random.randint(-40, 40),
                            follower.y + random.randint(-40, 40),
                            RED, 5, 50
                        ))
                elif not character.invulnerable and not character.invisible:
                    game_state = "game_over"
                    if score > high_score:
                        high_score = score

        spawn_timer += 1
        spawn_frequency = max(30, 120 - level * 5)
        if spawn_timer > spawn_frequency:
            spawn_timer = 0
            max_followers = 20 + level * 2
            if len(followers) < max_followers:
                side = random.randint(0, 3)
                if side == 0:
                    x, y = random.randint(0, SCREEN_WIDTH), -50
                elif side == 1:
                    x, y = random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + 50
                elif side == 2:
                    x, y = -50, random.randint(0, SCREEN_HEIGHT)
                else:
                    x, y = SCREEN_WIDTH + 50, random.randint(0, SCREEN_HEIGHT)

                if level < 5:
                    follower_type = "normal"
                elif level < 10:
                    follower_type = random.choice(["normal", "normal", "fast"])
                else:
                    follower_type = random.choice(["normal", "fast", "tank"])

                followers.append(Follower(
                    x, y,
                    random.randint(2, 4 + level // 3),
                    random.choice([RED, GREEN, BLUE, PURPLE, ORANGE, PINK]),
                    random.randint(40, 60),
                    follower_type
                ))

        coin_timer += 1
        if coin_timer > 80:
            coin_timer = 0
            coin_type = "normal"
            if random.randint(1, 100) <= 5:
                coin_type = "gold"
            elif random.randint(1, 100) <= 15:
                coin_type = "silver"

            coins.append(Coin(
                random.randint(50, SCREEN_WIDTH - 50),
                random.randint(50, SCREEN_HEIGHT - 50),
                coin_type
            ))

        powerup_timer += 1
        if powerup_timer > 400:
            powerup_timer = 0
            power_type = random.choice([
                POWER_SPEED, POWER_SHIELD, POWER_MAGNET, POWER_FREEZE,
                POWER_LIGHTNING, POWER_MULTIPLY, POWER_GIANT, POWER_INVISIBLE
            ])
            power_ups.append(PowerUp(
                random.randint(50, SCREEN_WIDTH - 50),
                random.randint(50, SCREEN_HEIGHT - 50),
                power_type
            ))

        for coin in coins[:]:
            if coin.update(character):
                coins.remove(coin)
                bonus = coin.value
                if combo > 0:
                    bonus = int(coin.value * (1 + combo * 0.1))
                score += bonus
                combo += 1
                max_combo = max(max_combo, combo)
                combo_timer = 120

                color = GOLD if coin.type == "gold" else SILVER if coin.type == "silver" else YELLOW
                floating_texts.append(FloatingText(
                    coin.x, coin.y, f"+{bonus} x{combo}", color, 24
                ))

                for _ in range(8):
                    particles.append(Particle(coin.x, coin.y, color, 3, 40))

        for power_up in power_ups[:]:
            if power_up.update(character):
                power_ups.remove(power_up)
                if power_up.power_type == POWER_MULTIPLY:
                    score *= 2
                    floating_texts.append(FloatingText(
                        power_up.x, power_up.y, "SCORE x2!", GOLD, 36
                    ))
                else:
                    character.activate_power(power_up.power_type)
                    floating_texts.append(FloatingText(
                        power_up.x, power_up.y, power_up.power_type.upper(), power_up.color, 28
                    ))

                shake_manager.add_shake(5, 20)
                for _ in range(12):
                    particles.append(Particle(power_up.x, power_up.y, power_up.color, 4, 50))

        for particle in particles[:]:
            particle.update()
            if particle.life <= 0:
                particles.remove(particle)

        for explosion in explosions[:]:
            explosion.update()
            if explosion.life <= 0:
                explosions.remove(explosion)

        for text in floating_texts[:]:
            text.update()
            if text.life <= 0:
                floating_texts.remove(text)

        for lightning in lightning_bolts[:]:
            lightning.update()
            if lightning.life <= 0:
                lightning_bolts.remove(lightning)

    GameDisplay.fill(BLACK)

    for x in range(0, SCREEN_WIDTH, 60):
        pygame.draw.line(GameDisplay, (20, 20, 20), (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, 60):
        pygame.draw.line(GameDisplay, (20, 20, 20), (0, y), (SCREEN_WIDTH, y))

    if game_state == "playing":
        for coin in coins:
            coin.draw(GameDisplay)

        for power_up in power_ups:
            power_up.draw(GameDisplay)

        for follower in followers:
            follower.draw(GameDisplay)

        if boss:
            boss.draw(GameDisplay)

        character.draw(GameDisplay)

        for particle in particles:
            particle.draw(GameDisplay)

        for explosion in explosions:
            explosion.draw(GameDisplay)

        for lightning in lightning_bolts:
            lightning.draw(GameDisplay)

        for text in floating_texts:
            text.draw(GameDisplay)

        score_text = font.render(f"Score: {score:,}", True, WHITE)
        level_text = font.render(f"Level: {level}", True, WHITE)
        time_text = font.render(f"Time: {time_survived // 60}s", True, WHITE)
        combo_text = font.render(f"Combo: {combo} (Max: {max_combo})", True, YELLOW)

        GameDisplay.blit(score_text, (10, 10))
        GameDisplay.blit(level_text, (10, 50))
        GameDisplay.blit(time_text, (10, 90))
        GameDisplay.blit(combo_text, (10, 130))

        if boss_mode and boss:
            boss_text = font.render("BOSS FIGHT!", True, RED)
            GameDisplay.blit(boss_text, (SCREEN_WIDTH // 2 - 80, 10))

        y_offset = 170
        for power_type, timer in character.power_timers.items():
            color = WHITE
            if power_type == POWER_SPEED:
                color = GREEN
            elif power_type == POWER_SHIELD:
                color = BLUE
            elif power_type == POWER_MAGNET:
                color = PURPLE
            elif power_type == POWER_FREEZE:
                color = CYAN
            elif power_type == POWER_LIGHTNING:
                color = YELLOW
            elif power_type == POWER_GIANT:
                color = RED
            elif power_type == POWER_INVISIBLE:
                color = GRAY

            power_text = small_font.render(f"{power_type.upper()}: {timer // 60}s", True, color)
            GameDisplay.blit(power_text, (10, y_offset))
            y_offset += 25

        follower_count = font.render(f"Enemies: {len(followers)}", True, WHITE)
        GameDisplay.blit(follower_count, (SCREEN_WIDTH - 200, 10))

        if character.dash_cooldown == 0:
            dash_text = small_font.render("DASH READY (SPACE)", True, GREEN)
            GameDisplay.blit(dash_text, (SCREEN_WIDTH - 200, 50))

        if combo > 10:
            combo_bonus_text = big_font.render(f"COMBO BONUS x{combo}!", True, GOLD)
            text_rect = combo_bonus_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
            GameDisplay.blit(combo_bonus_text, text_rect)

    elif game_state == "game_over":
        game_over_text = huge_font.render("GAME OVER", True, RED)
        final_score_text = font.render(f"Final Score: {score:,}", True, WHITE)
        high_score_text = font.render(f"High Score: {high_score:,}", True, GOLD)
        max_combo_text = font.render(f"Max Combo: {max_combo}", True, YELLOW)
        level_text = font.render(f"Level Reached: {level}", True, WHITE)
        time_text = font.render(f"Time Survived: {time_survived // 60}s", True, WHITE)
        restart_text = font.render("Press SPACE to restart", True, WHITE)

        GameDisplay.blit(game_over_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 150))
        GameDisplay.blit(final_score_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 80))
        GameDisplay.blit(high_score_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))
        GameDisplay.blit(max_combo_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 20))
        GameDisplay.blit(level_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 10))
        GameDisplay.blit(time_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 40))
        GameDisplay.blit(restart_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 80))

    offset_display = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    offset_display.blit(GameDisplay, shake_offset)
    GameDisplay.blit(offset_display, (0, 0))

    pygame.display.flip()

pygame.quit()
sys.exit()