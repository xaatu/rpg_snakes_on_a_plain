import pygame
from sprites import *
from config import *
import sys
import os

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(resource_path('fonts/UbuntuMono-Bold.ttf'), 50)
        self.tree_collision_font = pygame.font.Font(resource_path('fonts/UbuntuMono-Bold.ttf'), 15)

        self.character_spritesheet = Spritesheet(resource_path('img/character.png'))
        self.terrain_spritesheet = Spritesheet(resource_path('img/terrain.png'))
        self.enemy_spritesheet = Spritesheet(resource_path('img/enemy.png'))
        self.attack_spritesheet = Spritesheet(resource_path('img/attack.png'))
        self.intro_background = pygame.image.load(resource_path('img/introbackground4.png'))
        self.go_background = pygame.image.load(resource_path('img/gameover2.png'))
        self.win_background = pygame.image.load(resource_path('img/sky.png')).convert()

        # INIT LEVEL
        self.level = 1  # START AT 1
        self.inventory = Inventory(self)  
        self.items = Group()  
        self.trees = pygame.sprite.Group()  
        self.message = None  
        self.message_timer = 2
        self.camera = pygame.Vector2(0, 0)  
        self.score = 0  
        self.enemy_count = 0 


    def createTilemap(self):
        # CHOOSE TILEMAP BASED ON LEVEL - NEED TO CHANGE THIS WHEN EXTRA LEVELS
        if self.level == 1:
            terrain_tilemap = tilemap
            item_tilemap = itemmap
        elif self.level == 2:
            terrain_tilemap = tilemap2
            item_tilemap = itemmap2
        elif self.level == 3:
            terrain_tilemap = tilemap3
            item_tilemap = itemmap3
        elif self.level == 4:
            terrain_tilemap = tilemap4
            item_tilemap = itemmap4
        else:
            terrain_tilemap = tilemap5
            item_tilemap = itemmap5
        
            


        # CREATE TILES BASED ON CURRENT TERRAIN TILEMAP
        for i, row in enumerate(terrain_tilemap):
            for j, column in enumerate(row):
                if column == 'G':
                    Ground(self, j, i)
                if column == 'D':
                    Dirt(self, j, i)

        # CREATE ITEMS AND CHARACTERS BASED ON ITEM TILEMAP
        for i, row in enumerate(item_tilemap):
            for j, column in enumerate(row):
                if column == 'P':
                    self.player = Player(self, j, i)
                if column == 'E':
                    Enemy(self, j, i)
                if column == 'B':
                    Block(self, j, i)
                if column == 'T':
                    tree = Tree(self, j, i)
                    self.trees.add(tree)  
                if column == 'A':
                    Axe(self, j, i)
                

    def new(self):
        self.playing = True

        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.blocks = pygame.sprite.LayeredUpdates()
        self.enemies = pygame.sprite.LayeredUpdates()
        self.attacks = pygame.sprite.LayeredUpdates()

        # CURRENT LEVEL TILEMAP
        self.createTilemap()

        # LEVEL 1 MESSAGE
        if self.level == 1:
            self.display_message("Kill all the snakes to advance to the next level!", 180, font=self.tree_collision_font)  # 3 SECS

    def events(self):
        # GAME LOOP EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.playing = False
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.player.facing == 'up':
                        Attack(self, self.player.rect.x, self.player.rect.y - TILESIZE)
                    if self.player.facing == 'down':
                        Attack(self, self.player.rect.x, self.player.rect.y + TILESIZE)
                    if self.player.facing == 'left':
                        Attack(self, self.player.rect.x - TILESIZE, self.player.rect.y)
                    if self.player.facing == 'right':
                        Attack(self, self.player.rect.x + TILESIZE, self.player.rect.y)

                if event.key == pygame.K_c:  
                    hits = pygame.sprite.spritecollide(self.player, self.trees, False)  
                    for hit in hits:
                        if isinstance(hit, Tree):
                            if self.player.has_axe():
                                hit.kill()
                                print("Tree cut down!") 
                            else:
                                self.display_message("You need an axe to cut this tree!", 12, font=self.tree_collision_font)

    def update(self):
        self.all_sprites.update()
        self.items.update()  
        self.check_item_pickup() 

        # CHECK THERES NO ENEMIES
        if not self.enemies:
            # NEXT LEVEL WHEN NO MORE ENEMIES
            self.level += 1
            if self.level > 5:  # GAME OVER IF NO MORE LEVELS - NEED TO CHANGE THIS WITH EXTRA LEVELS
                self.win_screen()  # WIN IF ALL LEVELS DONE
            else:
                # CLEAR CURRENT LEVEL START NEXT
                for sprite in self.all_sprites:
                    sprite.kill()
                self.new()  

        if self.message_timer > 0:
            self.message_timer -= 1  
        else:
            self.message = None  

    def check_item_pickup(self):
        # CHECK COLLISION WITH ITEMS
        hits = pygame.sprite.spritecollide(self.player, self.items, True)
        for hit in hits:
            self.inventory.add_item(hit)  # ADD ITEM TO INV

    def draw(self):
        # Calculate camera position
        self.camera.x = self.player.rect.centerx - (WIN_WIDTH // 2)
        self.camera.y = self.player.rect.centery - (WIN_HEIGHT // 2)

        self.screen.fill(BLACK)
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, sprite.rect.topleft - self.camera)
        
        # CAMERA OFFSET ITEMS
        for item in self.items:
            self.screen.blit(item.image, item.rect.topleft - self.camera)

        self.inventory.draw() 

        # SCORE TOP RIGHT
        score_surface = self.font.render(f'Score: {self.score}', True, WHITE)
        score_rect = score_surface.get_rect(topright=(self.screen.get_width() - 10, 10))
        self.screen.blit(score_surface, score_rect)

        # DRAW MESSAGES
        if self.message:
            message_surface = self.font_to_use.render(self.message, True, WHITE)
            message_rect = message_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 50))
            self.screen.blit(message_surface, message_rect)

        self.clock.tick(FPS)
        pygame.display.update()

    def main(self):
        # MAIN GAME LOOP
        while self.playing:
            self.events()
            self.update()
            self.draw()

    def reset_game(self):
        self.level = 1  # START AT 1
        self.inventory = Inventory(self)  
        self.items = Group()  
        self.trees = pygame.sprite.Group()  
        self.message = None  
        self.message_timer = 2
        self.camera = pygame.Vector2(0, 0)  
        self.score = 0  
        self.enemy_count = 0 

    def game_over(self):
        text = self.font.render('Game Over', True, WHITE)
        text_rect = text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 50))

        # RESTART BUTTON
        restart_button = Button(
            x=self.screen.get_width() // 2 - 60,  
            y=text_rect.bottom + 20, 
            width=120,
            height=50,
            fg=WHITE,
            bg=BLACK,
            content='Restart',
            fontsize=32
        )

        for sprite in self.all_sprites:
            sprite.kill()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.playing = False

            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()

            if restart_button.is_pressed(mouse_pos, mouse_pressed):
                self.reset_game()  
                self.new()
                self.main()

            self.screen.blit(self.go_background, (0, 0))
            self.screen.blit(text, text_rect)
            self.screen.blit(restart_button.image, restart_button.rect)
            self.clock.tick(FPS)
            pygame.display.update()

    def intro_screen(self):
        intro = True

        title = self.font.render("SNAKES ON A PLAIN ", True, BLACK)
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 50))
        

        play_button = Button(
            x=self.screen.get_width() // 2 - 50, 
            y=title_rect.bottom + 20, 
            width=100,
            height=50,
            fg=WHITE,
            bg=BLACK,
            content='Play',
            fontsize=32
        )

        while intro:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    intro = False
                    self.running = False

            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()

            if play_button.is_pressed(mouse_pos, mouse_pressed):
                intro = False

            self.screen.blit(self.intro_background, (0, 0))
            self.screen.blit(title, title_rect)
            self.screen.blit(play_button.image, play_button.rect)
            self.clock.tick(FPS)
            pygame.display.update()

    def load_tilemap(self, tilemap):
        for y, row in enumerate(tilemap):
            for x, tile in enumerate(row):
                if tile == "T": 
                    tree = Tree(self, x * TILESIZE, y * TILESIZE) 
                    self.all_sprites.add(tree)  
                # ADD ITEM TYPES WHEN ADDED TO SPRITES

    def win_screen(self):
        text = self.font.render('Congratulations, You Win!', True, WHITE)
        text_rect = text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 50))

        # RESTART BUTTON
        restart_button = Button(
            x=self.screen.get_width() // 2 - 60,  
            y=text_rect.bottom + 20, 
            width=120,
            height=50,
            fg=WHITE,
            bg=BLACK,
            content='Restart',
            fontsize=32
        )

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.playing = False

            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()

            if restart_button.is_pressed(mouse_pos, mouse_pressed):
                self.reset_game()  
                self.new()
                self.main() 

            self.screen.blit(self.win_background, (0, 0)) 
            self.screen.blit(text, text_rect)
            self.screen.blit(restart_button.image, restart_button.rect)
            self.clock.tick(FPS)
            pygame.display.update()

    def display_message(self, message, duration=120, font=None):
        self.message = message  
        self.message_timer = duration 
        self.font_to_use = font if font else self.font  

# START GAME
g = Game()
g.intro_screen()
g.new()

# MAIN GAME LOOP
while g.running:
    g.main()
    if not g.playing:  # GAME OVER SCREEN IF GAME ENDS
        g.game_over()

pygame.quit()
sys.exit()

