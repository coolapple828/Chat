import pygame
import os
import math

pygame.init()

# Constants
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
FPS = 60
ROTATION_SPEED = 3
ACCELERATION = 0.2
MAX_SPEED = 6

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER_COLOR = (100, 149, 237)
SHOP_BG_COLOR = (30, 30, 30)

# Setup display
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Racers")
clock = pygame.time.Clock()

# Fonts
font = pygame.font.Font(None, 36)
title_font = pygame.font.Font(None, 72)

# Load background image (if available)
bg_path = os.path.join("CarGame/images/background.png")
if os.path.exists(bg_path):
    background = pygame.image.load(bg_path).convert_alpha()
    background = pygame.transform.scale(background, (WINDOW_WIDTH, WINDOW_HEIGHT))
else:
    background = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    background.fill(BLACK)

# --- UI Classes ---
class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.base_color = BUTTON_COLOR
        self.hover_color = BUTTON_HOVER_COLOR
        self.current_color = self.base_color
        self.font = font

    def update(self, events):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            self.current_color = self.hover_color
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.callback()
        else:
            self.current_color = self.base_color

    def draw(self, surface):
        draw_rect = self.rect.copy()
        if self.current_color == self.hover_color:
            draw_rect.inflate_ip(10, 10)
        pygame.draw.rect(surface, self.current_color, draw_rect, border_radius=8)
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=draw_rect.center)
        surface.blit(text_surface, text_rect)

# --- Game Classes ---
class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.original_image = pygame.image.load("CarGame/images/car.png").convert_alpha()
        scale_factor = 1 / 3
        new_width = int(self.original_image.get_width() * scale_factor)
        new_height = int(self.original_image.get_height() * scale_factor)
        self.scaled_image = pygame.transform.scale(self.original_image, (new_width, new_height))
        self.image = self.scaled_image
        self.rect = self.image.get_rect(center=pos)
        self.position = pygame.Vector2(self.rect.center)
        self.angle = 0
        self.speed = 0
        self.velocity = pygame.Vector2(0, 0)

    def update(self, border_sprites):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle += ROTATION_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle -= ROTATION_SPEED

        direction = pygame.Vector2(1, 0).rotate(-self.angle)

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed = min(self.speed + ACCELERATION, MAX_SPEED)
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed = max(self.speed - ACCELERATION, -MAX_SPEED/2)
        else:
            self.speed *= 0.98

        self.velocity = direction * self.speed
        self.position += self.velocity
        self.rect.center = self.position

        # Window boundaries
        if self.rect.left < 0:
            self.rect.left = 0
            self.position.x = self.rect.centerx
        if self.rect.right > WINDOW_WIDTH:
            self.rect.right = WINDOW_WIDTH
            self.position.x = self.rect.centerx
        if self.rect.top < 0:
            self.rect.top = 0
            self.position.y = self.rect.centery
        if self.rect.bottom > WINDOW_HEIGHT:
            self.rect.bottom = WINDOW_HEIGHT
            self.position.y = self.rect.centery

        for border in border_sprites:
            if self.rect.colliderect(border.rect):
                self.position -= self.velocity
                self.rect.center = self.position
                self.speed = 0

        # Rotate the image so the front is aligned
        self.image = pygame.transform.rotate(self.scaled_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

class Border(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

class FinishLine(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image.fill((255, 0, 0))  # Red finish line
        self.rect = self.image.get_rect(center=(x, y))

# --- Shop Classes ---
class ShopItem:
    def __init__(self, name, description, price, image=None):
        self.name = name
        self.description = description
        self.price = price
        self.image = image

    def draw(self, surface, pos):
        item_text = font.render(self.name, True, WHITE)
        surface.blit(item_text, pos)

# --- State Management ---
current_state = "menu"

def change_state(new_state):
    global current_state
    current_state = new_state

# --- State Functions ---
def main_menu():
    global current_state
    running = True

    start_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 40, 200, 50, "Start Game", lambda: change_state("game"))
    shop_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 30, 200, 50, "Shop", lambda: change_state("shop"))

    alpha = 0
    fade_in = True

    while running and current_state == "menu":
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        if fade_in:
            alpha += 5
            if alpha >= 255:
                alpha = 255
                fade_in = False
        else:
            alpha -= 5
            if alpha <= 100:
                alpha = 100
                fade_in = True

        start_button.update(events)
        shop_button.update(events)

        screen.blit(background, (0, 0))
        title_surface = title_font.render("Racers", True, WHITE)
        title_surface.set_alpha(alpha)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 150))
        screen.blit(title_surface, title_rect)
        start_button.draw(screen)
        shop_button.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

        if current_state != "menu":
            running = False

def shop_menu():
    global current_state
    running = True
    scroll_offset = 0
    shop_items = []  # Empty for now; add ShopItem objects later

    back_button = Button(50, 50, 150, 40, "Back", lambda: change_state("menu"))
    shop_frame_rect = pygame.Rect(200, 150, WINDOW_WIDTH - 400, WINDOW_HEIGHT - 300)
    shop_frame_surface = pygame.Surface((shop_frame_rect.width, shop_frame_rect.height))
    shop_frame_surface.fill(SHOP_BG_COLOR)

    while running and current_state == "shop":
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEWHEEL:
                scroll_offset += event.y * 20

        scroll_offset = max(min(scroll_offset, 0), -300)

        back_button.update(events)
        screen.fill(BLACK)
        shop_title = title_font.render("Shop", True, WHITE)
        shop_title_rect = shop_title.get_rect(center=(WINDOW_WIDTH//2, 80))
        screen.blit(shop_title, shop_title_rect)

        pygame.draw.rect(screen, WHITE, shop_frame_rect, 2, border_radius=8)
        shop_frame_surface.fill(SHOP_BG_COLOR)

        y = 10 + scroll_offset
        for item in shop_items:
            item.draw(shop_frame_surface, (10, y))
            y += 60

        screen.blit(shop_frame_surface, shop_frame_rect.topleft)
        back_button.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

        if current_state != "shop":
            running = False

def game_loop():
    global current_state
    all_sprites = pygame.sprite.Group()
    border_sprites = pygame.sprite.Group()

    player = Player((WINDOW_WIDTH//2 + 100, 500))
    all_sprites.add(player)
    border = Border(WINDOW_WIDTH//2, WINDOW_HEIGHT//2, 540, 20)
    all_sprites.add(border)
    border_sprites.add(border)

    # Create a finish line near the top of the track
    finish_line = FinishLine(WINDOW_WIDTH//2 - 20, 500, 20, 80)
    all_sprites.add(finish_line)

    lap_count = 0
    lap_triggered = False

    running = True
    while running and current_state == "game":
        dt = clock.tick(FPS) / 1000
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                change_state("menu")
                running = False

        screen.blit(background, (0, 0))
        all_sprites.update(border_sprites)

        # Lap detection: if the player's car collides with the finish line,
        # and hasn't already been counted on this pass, increment lap count.
        if player.rect.colliderect(finish_line.rect):
            if not lap_triggered:
                lap_count += 1
                lap_triggered = True
        else:
            lap_triggered = False

        # Draw lap count on screen
        lap_text = font.render(f"Laps: {lap_count}", True, WHITE)
        screen.blit(lap_text, (20, 20))

        all_sprites.draw(screen)
        pygame.display.flip()

        # If three laps have been completed, display win message and return to menu
        if lap_count >= 3:
            win_text = title_font.render("You Win!", True, WHITE)
            win_rect = win_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
            screen.blit(win_text, win_rect)
            pygame.display.flip()
            pygame.time.delay(3000)
            change_state("menu")
            running = False

def main():
    global current_state
    while True:
        if current_state == "menu":
            main_menu()
        elif current_state == "shop":
            shop_menu()
        elif current_state == "game":
            game_loop()

if __name__ == "__main__":
    main()
