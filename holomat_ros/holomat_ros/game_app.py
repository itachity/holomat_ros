# game_app.py
import pygame
import math
import time
from pygame import mixer

def run(screen, camera_manager, publish_event_fn):
    """
    A combined Space Invaders and Brick Breaker app. Uses the index finger (landmark8) to move
    the player/paddle. Pinch automatically fires (for Space Invaders).
    Hover Home (bottom‐left) to exit back to home.
    """
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    BLACK = (0,0,0)
    WHITE = (255,255,255)
    LIGHT_BLUE = (173,216,230)
    RED = (255,0,0)
    NAVY_BLUE = (20,20,40)

    def distance(p1, p2):
        return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

    # Load images & sounds
    player_img = pygame.image.load("apps/app_2/player.png")
    invader1_img = pygame.image.load("apps/app_2/invader1.png")
    invader2_img = pygame.image.load("apps/app_2/invader2.png")
    player_img = pygame.transform.scale(player_img, (player_img.get_width()*8, player_img.get_height()*8))
    invader1_img = pygame.transform.scale(invader1_img, (invader1_img.get_width()*3, invader1_img.get_height()*3))
    invader2_img = pygame.transform.scale(invader2_img, (invader2_img.get_width()*3, invader2_img.get_height()*3))

    # Preload sounds
    def sfx(path):
        try:
            mixer.music.load(path)
            mixer.music.play()
        except:
            pass

    # -------- SPACE INVADERS SETUP --------
    player_w, player_h = player_img.get_size()
    player = pygame.Rect(SCREEN_WIDTH//2 - player_w//2, SCREEN_HEIGHT - player_h - 10, player_w, player_h)
    bullets = []
    invaders = []
    for row in range(5):
        for col in range(11):
            x = col*(invader1_img.get_width()+15) + 150
            y = row*(invader1_img.get_height()+15) + 50
            rect = pygame.Rect(x,y, invader1_img.get_width(), invader1_img.get_height())
            if row < 3:
                invaders.append((rect, invader1_img))
            else:
                invaders.append((rect, invader2_img))
    inv_dir = 1
    inv_speed_x = 3
    inv_drop = 10
    can_shoot = True

    # -------- BRICK BREAKER SETUP (will only run if user chooses) --------
    # We’ll simplify: after Space Invaders ends, switch to Brick Breaker.
    def run_brick_breaker():
        ball_dx, ball_dy = 7, -7
        paddle = pygame.Rect(SCREEN_WIDTH//2 - 75, SCREEN_HEIGHT-50, 150, 20)
        ball = pygame.Rect(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 20, 20)
        bricks = []
        for row in range(5):
            for col in range(SCREEN_WIDTH//125):
                bricks.append(pygame.Rect(col*125, row*30+50, 120, 25))
        clock = pygame.time.Clock()
        playing = True
        while playing:
            camera_manager.update()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE):
                    playing = False
                    break

            screen.fill(BLACK)
            hands = camera_manager.get_transformed_landmarks()
            if hands:
                idx = hands[0][8]
                if idx:
                    paddle.centerx = idx[0]
            # Ball movement
            ball.x += ball_dx; ball.y += ball_dy
            if ball.left<=0 or ball.right>=SCREEN_WIDTH:
                sfx("audio/bounce.mp3")
                ball_dx *= -1
            if ball.top<=0:
                sfx("audio/bounce.mp3")
                ball_dy *= -1
            if ball.bottom>=SCREEN_HEIGHT:
                # lost → reset everything
                paddle.x = SCREEN_WIDTH//2-75; ball.x, ball.y = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
                bricks.clear()
                for row in range(5):
                    for col in range(SCREEN_WIDTH//125):
                        bricks.append(pygame.Rect(col*125, row*30+50, 120, 25))
                ball_dx, ball_dy = 7, -7

            if ball.colliderect(paddle):
                sfx("audio/bounce.mp3")
                ball_dy *= -1

            for b in bricks[:]:
                if ball.colliderect(b):
                    sfx("audio/explosion.mp3")
                    bricks.remove(b)
                    ball_dy *= -1
                    break

            # Draw everything
            pygame.draw.rect(screen, WHITE, paddle)
            pygame.draw.ellipse(screen, (0,0,255), ball)
            for b in bricks:
                pygame.draw.rect(screen, RED, b)

            # Home button bottom‐left
            HOME_BTN = (50, SCREEN_HEIGHT-50)
            if hands and hands[0][8]:
                if distance(hands[0][8], HOME_BTN) <= 50:
                    publish_event_fn("GAME_HOME_PRESSED")
                    playing = False

            pygame.draw.circle(screen, NAVY_BLUE, HOME_BTN, 50)
            pygame.draw.circle(screen, WHITE, HOME_BTN, 50, 5)
            font = pygame.font.Font(None, 36)
            txt = font.render("Home", True, WHITE)
            screen.blit(txt, (HOME_BTN[0]-25, HOME_BTN[1]-15))

            pygame.display.flip()
            clock.tick(60)

    # -------- RUN SPACE INVADERS FIRST --------
    clock = pygame.time.Clock()
    running = True
    while running:
        camera_manager.update()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE):
                running = False
                break

        screen.fill(BLACK)
        hands = camera_manager.get_transformed_landmarks()
        if hands:
            idx = hands[0][8]
            if idx:
                player.centerx = idx[0]
        # Fire bullets automatically
        if can_shoot:
            sfx("audio/laser.mp3")
            bullets.append(pygame.Rect(player.centerx-2, player.top-10, 5, 10))
            can_shoot = False

        for b in bullets[:]:
            b.y -= 10
            if b.bottom < 0:
                bullets.remove(b)
                can_shoot = True

        # Move invaders
        move_down = False
        for inv, img in invaders:
            inv.x += inv_speed_x * inv_dir
            if inv.left <= 0 or inv.right >= SCREEN_WIDTH:
                move_down = True
        if move_down:
            inv_dir *= -1
            for inv, _ in invaders:
                inv.y += inv_drop
                inv.x += inv_speed_x * inv_dir
            inv_speed_x *= 1.05

        # Bullet collisions
        for b in bullets[:]:
            for inv, img in invaders[:]:
                if b.colliderect(inv):
                    sfx("audio/explosion.mp3")
                    invaders.remove((inv,img))
                    bullets.remove(b)
                    can_shoot = True
                    break

        # Draw invaders & player & bullets
        for inv, img in invaders:
            screen.blit(img, inv.topleft)
        screen.blit(player_img, player.topleft)
        for b in bullets:
            pygame.draw.rect(screen, RED, b)

        # Home button (top‐left)
        HOME_BTN = (50,50)
        if hands and hands[0][8]:
            if distance(hands[0][8], HOME_BTN) <= 50:
                publish_event_fn("GAME_HOME_PRESSED")
                running = False

        pygame.draw.circle(screen, NAVY_BLUE, HOME_BTN, 50)
        pygame.draw.circle(screen, LIGHT_BLUE, HOME_BTN, 50, 5)
        font = pygame.font.Font(None, 36)
        screen.blit(font.render("Home", True, WHITE), (HOME_BTN[0]-25, HOME_BTN[1]-15))

        # Win/Lose conditions
        if not invaders:
            screen.blit(font.render("YOU WIN!", True, WHITE), (SCREEN_WIDTH//2-80, SCREEN_HEIGHT//2-20))
            pygame.display.flip()
            pygame.time.delay(2000)
            running = False
        elif any(inv.bottom >= SCREEN_HEIGHT for inv,_ in invaders):
            screen.blit(font.render("GAME OVER", True, WHITE), (SCREEN_WIDTH//2-100, SCREEN_HEIGHT//2-20))
            pygame.display.flip()
            pygame.time.delay(2000)
            running = False

        pygame.display.flip()
        clock.tick(60)

    # After space invaders ends, automatically switch to brick breaker
    run_brick_breaker()
    return
