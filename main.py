import pygame
import sys
import math
import random

pygame.init()
pygame.mixer.init()

# Impostazione Schermo Pieno Schermo Dinamico
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()

# Costanti
FPS = 60
SEGMENT_LENGTH = 200

# Colori
GRASS_LIGHT = (34, 139, 34)
GRASS_DARK = (0, 100, 0)
ROAD_LIGHT = (160, 104, 60) # Terra chiara per motocross
ROAD_DARK = (139, 90, 43)   # Terra scura
RUMBLE_LIGHT = (255, 255, 255)
RUMBLE_DARK = (200, 0, 0)
SKY_COLOR = (135, 206, 235)

pygame.display.set_caption("Motocross 3D")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)
score_font = pygame.font.SysFont(None, 72)

# Caricamento asset
def load_image(path, scale_to=None, color_key="auto"):
    try:
        img = pygame.image.load(path).convert_alpha()
        
        if color_key == "auto":
            color_key = img.get_at((0, 0))
            
        if color_key is not None:
            temp = pygame.Surface(img.get_size(), pygame.SRCALPHA)
            img.set_colorkey(color_key)
            temp.blit(img, (0, 0))
            img = temp
            
        if scale_to:
            img = pygame.transform.scale(img, scale_to)
        return img
    except Exception as e:
        print(f"Errore caricamento {path}: {e}")
        surf = pygame.Surface(scale_to if scale_to else (100, 100), pygame.SRCALPHA)
        if "bike" in path:
            pygame.draw.rect(surf, (200, 0, 0), (surf.get_width()//4, surf.get_height()//2, surf.get_width()//2, surf.get_height()//2))
        elif "coin" in path:
            pygame.draw.circle(surf, (255, 215, 0), (surf.get_width()//2, surf.get_height()//2), surf.get_width()//2)
        return surf

bike_back_img = load_image("assets/bike_back_view.png", (250, 350), "auto")
bike_side_img = load_image("assets/bike.png", (800, 600), "auto")
coin_img = load_image("assets/coin.png", (160, 160), None)
bg_mountains_img = load_image("assets/bg_mountains.png", (WIDTH, HEIGHT), None)

class Line:
    def __init__(self, index):
        self.i = index
        self.x = 0 # Curva
        self.y = 0 # Altezza
        self.z = self.i * SEGMENT_LENGTH
        
        self.X = 0
        self.Y = 0
        self.W = 0
        self.scale = 0
        self.clip = HEIGHT # Per il clipping degli sprite
        
        self.curve = 0
        self.sprite = None
        self.spriteX = 0
        self.sprite_h = 0
        self.sprite_collected = False
        
        self.has_tree = False
        self.treeX = 0
        self.has_arch = False
        
    def project(self, relX, camY, camZ, loop_offset):
        dz = self.z + loop_offset - camZ
        if dz <= 0.1: dz = 0.1
        
        self.scale = 0.84 / dz
        self.X = (1 + self.scale * relX) * WIDTH / 2
        self.Y = (1 - self.scale * (self.y - camY)) * HEIGHT / 2
        self.W = self.scale * 2000 * WIDTH / 2

class Game:
    def __init__(self):
        self.lines = []
        self.generate_track()
        
        self.pos = 0 
        self.playerX = 0 # da -1 (sinistra) a 1 (destra)
        self.playerY = 0 # Altezza salto
        
        self.speed = 0
        self.base_speed = 5500
        
        self.is_jumping = False
        self.jump_velocity = 0
        self.last_up_press_time = 0
        self.is_flipping = False
        self.flip_angle = 0
        
        self.score = 0
        self.state = "SPLASH"
        self.lap = 1
        self.max_laps = 3
        self.sky_offset_x = 0
        
        # Testo per l'arco
        arch_font = pygame.font.SysFont(None, 200, bold=True)
        base_text = arch_font.render("START", True, (255, 0, 0))
        self.start_text_img = pygame.Surface((base_text.get_width() + 10, base_text.get_height() + 10), pygame.SRCALPHA)
        for dx, dy in [(-4,-4), (-4,4), (4,-4), (4,4), (0,-5), (0,5), (-5,0), (5,0)]:
            outline = arch_font.render("START", True, (255, 255, 255))
            self.start_text_img.blit(outline, (5 + dx, 5 + dy))
        self.start_text_img.blit(base_text, (5, 5))
        
        # Audio
        try:
            self.engine_sound = pygame.mixer.Sound("assets/bg_music.wav")
            self.coin_sound = pygame.mixer.Sound("assets/coin.wav")
            self.engine_sound.set_volume(0.4)
            self.coin_sound.set_volume(0.8)
        except Exception as e:
            print("Errore audio:", e)
            self.engine_sound = None
            self.coin_sound = None

    def generate_track(self):
        for i in range(1500):
            line = Line(i)
            
            # Colline più pronunciate
            line.y = math.sin(i / 15.0) * 1800
            
            # Curve distribuite su un tracciato più lungo
            if 100 < i < 250: line.curve = 2.0
            if 350 < i < 500: line.curve = -2.5
            if 650 < i < 800: line.curve = 2.2
            if 950 < i < 1100: line.curve = -2.0
            if 1250 < i < 1400: line.curve = 2.5
            
            # Monete
            if i > 20 and i % 20 == 0:
                line.sprite = coin_img
                line.spriteX = random.choice([-0.8, -0.4, 0, 0.4, 0.8])
                # Metti alcune monete in alto per saltare
                if random.random() < 0.25:
                    line.sprite_h = 3500
                
            # Alberi ai lati
            if i % 8 == 0:
                line.has_tree = True
                line.treeX = random.choice([-1.5, 1.5])
                
            if i == 80:
                line.has_arch = True
                
            self.lines.append(line)
            
        self.track_length = len(self.lines) * SEGMENT_LENGTH

    def draw_quad(self, color, x1, y1, w1, x2, y2, w2):
        if y1 <= y2: return # Evita poligoni rovesciati
        pygame.draw.polygon(screen, color, [
            (x1 - w1, y1),
            (x2 - w2, y2),
            (x2 + w2, y2),
            (x1 + w1, y1)
        ])

    def run(self):
        running = True
        while running:
            # 1. EVENTI
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if self.state == "SPLASH":
                        self.state = "PLAYING"
                        if self.engine_sound:
                            self.engine_sound.play(-1)
                    elif self.state == "GAMEOVER":
                        running = False
                    elif self.state == "PLAYING":
                        if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                            current_time = pygame.time.get_ticks()
                            
                            if event.key == pygame.K_UP:
                                if current_time - self.last_up_press_time < 400: # 400 ms per il doppio tap
                                    if self.is_jumping and not self.is_flipping:
                                        self.is_flipping = True
                                        self.flip_angle = 0
                                self.last_up_press_time = current_time

                            if not self.is_jumping:
                                self.is_jumping = True
                                self.jump_velocity = 400 # Salto più alto

            if self.state == "SPLASH":
                screen.fill(SKY_COLOR)
                
                # Sfondo erba decorativo
                pygame.draw.rect(screen, GRASS_DARK, (0, HEIGHT//2, WIDTH, HEIGHT//2))
                
                screen.blit(bike_side_img, (WIDTH//2 - bike_side_img.get_width()//2, HEIGHT//2 - bike_side_img.get_height()//2 - 50))
                
                title = font.render("MOTOCROSS 3D", True, (255, 215, 0))
                title_shadow = font.render("MOTOCROSS 3D", True, (0, 0, 0))
                
                prompt = font.render("Premi un tasto per iniziare", True, (255, 255, 255))
                prompt_shadow = font.render("Premi un tasto per iniziare", True, (0, 0, 0))
                
                screen.blit(title_shadow, (WIDTH//2 - title.get_width()//2 + 3, 153))
                screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
                
                screen.blit(prompt_shadow, (WIDTH//2 - prompt.get_width()//2 + 3, HEIGHT - 147))
                screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT - 150))
                
                pygame.display.flip()
                clock.tick(FPS)
                continue

            if self.state == "GAMEOVER":
                if getattr(self, 'engine_sound', None):
                    self.engine_sound.stop()
                screen.fill((0, 0, 0))
                title = font.render("GARA TERMINATA!", True, (255, 215, 0))
                score_msg = font.render(f"Punteggio: {self.score}", True, (255, 255, 255))
                prompt = font.render("Premi ESC per uscire o QUALSIASI TASTO per chiudere", True, (150, 150, 150))
                
                screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 100))
                screen.blit(score_msg, (WIDTH//2 - score_msg.get_width()//2, HEIGHT//2))
                screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 + 100))
                
                pygame.display.flip()
                clock.tick(FPS)
                continue

            # -- PLAYING --
            keys = pygame.key.get_pressed()
            
            # Accelerazione base costante + boost manuale
            self.speed = self.base_speed
            if keys[pygame.K_w]:
                self.speed += 2500
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.speed -= 2500
                
            if getattr(self, 'engine_sound', None):
                # Volume costante per la musica di sottofondo
                self.engine_sound.set_volume(0.4)

            # Sterzo
            if keys[pygame.K_LEFT]:
                self.playerX -= 0.04
                self.sky_offset_x += 4 # Parallasse sterzo
            if keys[pygame.K_RIGHT]:
                self.playerX += 0.04
                self.sky_offset_x -= 4 # Parallasse sterzo

            # Restrizioni pista (erba rallenta se vogliamo, qui semplicemente non lo facciamo uscire)
            self.playerX = max(-1.5, min(1.5, self.playerX))

            # Fisica Salto
            if self.is_jumping:
                self.playerY += self.jump_velocity
                self.jump_velocity -= 15 # Gravità
                if self.is_flipping:
                    self.flip_angle -= 8 # Velocità di rotazione per fare circa un 360
                if self.playerY <= 0:
                    self.playerY = 0
                    self.is_jumping = False
                    self.is_flipping = False
                    self.flip_angle = 0

            # Collisione Alberi
            check_idx = (int(self.pos / SEGMENT_LENGTH) + 1) % len(self.lines)
            check_line = self.lines[check_idx]
            if check_line.has_tree:
                if abs(self.playerX - check_line.treeX) < 0.4 and self.playerY < 1200:
                    self.speed = 0
                    self.pos -= 150 # Rimbalzo all'indietro per non incastrarsi
                    self.is_jumping = False
                    self.is_flipping = False
                    self.playerY = 0

            # Avanzamento
            self.pos += self.speed * (1/FPS)
            while self.pos >= self.track_length:
                self.pos -= self.track_length
                self.lap += 1
                if self.lap > self.max_laps:
                    self.state = "GAMEOVER"
                    if getattr(self, 'engine_sound', None):
                        self.engine_sound.stop()
            while self.pos < 0:
                self.pos += self.track_length

            # 3. DISEGNO 3D
            screen.fill(SKY_COLOR)
            
            startPos = int(self.pos / SEGMENT_LENGTH)
            
            # Parallasse basato sulla curva della pista
            current_line = self.lines[startPos % len(self.lines)]
            self.sky_offset_x -= current_line.curve * self.speed * 0.0003
            self.sky_offset_x = self.sky_offset_x % WIDTH
            
            # Disegno Sfondo Montagne (Scorrimento continuo)
            bg_x = int(self.sky_offset_x)
            screen.blit(bg_mountains_img, (bg_x, 0))
            screen.blit(bg_mountains_img, (bg_x - WIDTH, 0))
            percent = (self.pos % SEGMENT_LENGTH) / SEGMENT_LENGTH
            
            # Altezza Camera (segue il terreno)
            curr_y = self.lines[startPos % len(self.lines)].y
            next_y = self.lines[(startPos + 1) % len(self.lines)].y
            camY = curr_y + (next_y - curr_y) * percent
            camH = 1500 + camY
            
            camX = self.playerX * 2000
            
            # Controllo Monete
            current_line = self.lines[(startPos + 2) % len(self.lines)] # +2 per compensare il disegno
            if current_line.sprite is not None and not current_line.sprite_collected:
                # Se è una moneta alta, devi saltare
                height_ok = False
                if current_line.sprite_h > 0:
                    height_ok = self.playerY > 1500
                else:
                    height_ok = self.playerY < 3000

                if abs(current_line.spriteX - self.playerX) < 0.4 and height_ok:
                    current_line.sprite_collected = True
                    self.score += 10
                    if getattr(self, 'coin_sound', None):
                        self.coin_sound.play()

            x = 0
            dx = 0
            
            # Calcolo Proiezioni
            for n in range(300):
                idx = (startPos + n) % len(self.lines)
                l = self.lines[idx]
                
                l.x = x
                x += dx
                dx += l.curve
                
                loop_offset = self.track_length if (startPos + n) >= len(self.lines) else 0
                l.project(l.x - camX, camH, self.pos, loop_offset)
                
            # Disegno Pista (Painter's algorithm: Front to Back per clipping corretto)
            maxy = HEIGHT
            for n in range(1, 300):
                idx = (startPos + n) % len(self.lines)
                prev_idx = (startPos + n - 1) % len(self.lines)
                
                l = self.lines[idx]
                p = self.lines[prev_idx]
                
                l.clip = maxy
                
                if l.Y >= maxy: continue
                
                color_idx = (idx // 3) % 2
                grass = GRASS_LIGHT if color_idx else GRASS_DARK
                road = ROAD_LIGHT if color_idx else ROAD_DARK
                
                # Prato intero
                pygame.draw.rect(screen, grass, (0, l.Y, WIDTH, max(1, p.Y - l.Y)))
                
                # Strada
                self.draw_quad(road, p.X, p.Y, p.W, l.X, l.Y, l.W)
                
                maxy = l.Y
                
            # Disegno Sprite (Monete e Alberi) - Back to Front (painter's)
            for n in range(299, 0, -1):
                idx = (startPos + n) % len(self.lines)
                l = self.lines[idx]
                
                # Disegna Alberi
                if l.has_tree:
                    if l.Y < l.clip:
                        tree_world_x = l.x + l.treeX * 2000
                        relX_tree = tree_world_x - camX
                        treeX = (1 + l.scale * relX_tree) * WIDTH / 2
                        treeY = l.Y
                        
                        tw = int(600 * l.scale * 800) # Alberi ingranditi
                        th = int(1200 * l.scale * 800)
                        
                        if tw > 0 and th > 0:
                            # Tronco
                            pygame.draw.rect(screen, (101, 67, 33), (treeX - tw//6, treeY - th, tw//3, th))
                            # Chioma
                            pygame.draw.polygon(screen, (34, 139, 34), [
                                (treeX, treeY - th * 1.5),
                                (treeX - tw//2, treeY - th//2),
                                (treeX + tw//2, treeY - th//2)
                            ])
                
                # Disegna Monete
                if l.sprite is not None and not l.sprite_collected:
                    # Clip colline
                    if l.Y >= l.clip: continue
                    
                    sprite_world_x = l.x + l.spriteX * 2000
                    relX = sprite_world_x - camX
                    
                    spriteX = (1 + l.scale * relX) * WIDTH / 2
                    spriteY = l.Y - l.scale * l.sprite_h * HEIGHT / 2
                    
                    sw = int(l.sprite.get_width() * l.scale * 1500)
                    sh = int(l.sprite.get_height() * l.scale * 1500)
                    
                    if sw > 0 and sh > 0:
                        scaled = pygame.transform.scale(l.sprite, (sw, sh))
                        screen.blit(scaled, (spriteX - sw/2, spriteY - sh))

                # Disegna Arch
                if getattr(l, 'has_arch', False):
                    if l.Y < l.clip:
                        for col in range(10):
                            for row in range(8):
                                if (col == 0 or col == 9) and row < 6:
                                    pass
                                elif row >= 6:
                                    pass
                                else:
                                    continue
                                    
                                is_black = (col + row) % 2 == 0
                                color = (0, 0, 0) if is_black else (255, 255, 255)
                                
                                localX = -2500 + col * 500
                                worldX1 = l.x + localX
                                worldX2 = l.x + localX + 500
                                
                                sx1 = (1 + l.scale * (worldX1 - camX)) * WIDTH / 2
                                sx2 = (1 + l.scale * (worldX2 - camX)) * WIDTH / 2
                                
                                worldY1 = row * 500
                                worldY2 = row * 500 + 500
                                sy_bottom = l.Y - l.scale * worldY1 * HEIGHT / 2
                                sy_top = l.Y - l.scale * worldY2 * HEIGHT / 2
                                
                                rect_x = sx1
                                rect_w = sx2 - sx1
                                rect_y = sy_top
                                rect_h = sy_bottom - sy_top
                                
                                if rect_w > 0 and rect_h > 0 and rect_x < WIDTH and rect_x + rect_w > 0 and rect_y < HEIGHT and rect_y + rect_h > 0:
                                    pygame.draw.rect(screen, color, (rect_x, rect_y, rect_w + 1, rect_h + 1))
                                    
                        cx = (1 + l.scale * (l.x - camX)) * WIDTH / 2
                        cy = l.Y - l.scale * 3500 * HEIGHT / 2
                        
                        text_sw = int(l.scale * 3000 * WIDTH / 2)
                        if 0 < text_sw < WIDTH * 5:
                            text_sh = int(text_sw * self.start_text_img.get_height() / self.start_text_img.get_width())
                            if text_sh > 0:
                                scaled_text = pygame.transform.scale(self.start_text_img, (text_sw, text_sh))
                                screen.blit(scaled_text, (cx - text_sw/2, cy - text_sh/2))

            # Disegno Giocatore
            tilt = 0
            if keys[pygame.K_LEFT]: tilt = 10
            if keys[pygame.K_RIGHT]: tilt = -10
                
            bike_img = bike_back_img
            if self.is_flipping:
                bike_img = pygame.transform.rotate(bike_back_img, self.flip_angle)
            elif tilt != 0:
                bike_img = pygame.transform.rotate(bike_back_img, tilt)
                
            bw = bike_img.get_width()
            bh = bike_img.get_height()
            
            # Spostamento verticale in base al salto (playerY scalato)
            screen_bike_y = HEIGHT - bh - 60 - (self.playerY * 0.15)
            
            screen.blit(bike_img, (WIDTH/2 - bw/2, screen_bike_y))

            # Disegno Punteggio e Giri
            ui_text = f"Giro: {self.lap}/{self.max_laps}   Punteggio: {self.score}"
            score_surf = score_font.render(ui_text, True, (255, 255, 255))
            score_shadow = score_font.render(ui_text, True, (0, 0, 0))
            screen.blit(score_shadow, (22, 22))
            screen.blit(score_surf, (20, 20))

            pygame.display.flip()
            clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()
