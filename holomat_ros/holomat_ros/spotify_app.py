# spotify_app.py
import pygame
import time
from pygame import mixer

# You must install spotipy or another Spotify API wrapper,
# configure CLIENT_ID/CLIENT_SECRET + redirect URI in your environment/.env,
# and authenticate once to get a refresh token.

def run(screen, camera_manager, publish_event_fn):
    """
    A basic Spotify controller UI. For example:
      - Hover your index finger over “Play/Pause” button to toggle,
      - Hover over “Next” to skip track, “Prev” to previous,
      - Maybe show current track metadata on screen.
    """
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    BLACK = (0,0,0)
    WHITE = (255,255,255)
    LIGHT_BLUE = (173,216,230)
    NAVY_BLUE = (20,20,40)

    # Layout: three circles horizontally:
    #  • Prev (x=SCREEN_WIDTH//4, y=SCREEN_HEIGHT//2)
    #  • Play/Pause (x=SCREEN_WIDTH//2, y=SCREEN_HEIGHT//2)
    #  • Next (x=3*SCREEN_WIDTH//4, y=SCREEN_HEIGHT//2)
    RADIUS = 100
    POS_PREV = (SCREEN_WIDTH//4, SCREEN_HEIGHT//2)
    POS_PLAY = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    POS_NEXT = (3*SCREEN_WIDTH//4, SCREEN_HEIGHT//2)
    POS_HOME = (50,50)  # Home circle

    def is_hover(p, center):
        return (p[0]-center[0])**2 + (p[1]-center[1])**2 <= RADIUS*RADIUS

    def toggle_play_pause():
        # call Spotify API to toggle playback
        pass

    def skip_next():
        # call Spotify API to skip track
        pass

    def skip_prev():
        # call Spotify API to previous track
        pass

    clock = pygame.time.Clock()
    index_pos = None
    last_action = 0
    HOVER_DELAY = 1.0

    while True:
        camera_manager.update()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE):
                return

        screen.fill(BLACK)
        hands = camera_manager.get_transformed_landmarks()
        if hands:
            idx = hands[0][8]
            if idx:
                index_pos = idx
                pygame.draw.circle(screen, LIGHT_BLUE, index_pos, 15, 3)

        now = time.time()

        # Draw Prev/Play/Next circles
        pygame.draw.circle(screen, NAVY_BLUE, POS_PREV, RADIUS)
        pygame.draw.circle(screen, WHITE, POS_PREV, RADIUS, 5)
        pygame.draw.circle(screen, NAVY_BLUE, POS_PLAY, RADIUS)
        pygame.draw.circle(screen, WHITE, POS_PLAY, RADIUS, 5)
        pygame.draw.circle(screen, NAVY_BLUE, POS_NEXT, RADIUS)
        pygame.draw.circle(screen, WHITE, POS_NEXT, RADIUS, 5)

        # Draw Home
        pygame.draw.circle(screen, NAVY_BLUE, POS_HOME, RADIUS//2)
        pygame.draw.circle(screen, WHITE, POS_HOME, RADIUS//2, 5)
        font = pygame.font.Font(None, 36)
        txt = font.render("Home", True, WHITE)
        rect = txt.get_rect(center=POS_HOME)
        screen.blit(txt, rect)

        # If user hovers index finger for ≥ 1 s on any button, fire the action:
        if index_pos:
            # PREV
            if is_hover(index_pos, POS_PREV):
                if now - last_action > HOVER_DELAY:
                    skip_prev()
                    publish_event_fn("SPOTIFY_PREV")
                    last_action = now

            # PLAY/PAUSE
            if is_hover(index_pos, POS_PLAY):
                if now - last_action > HOVER_DELAY:
                    toggle_play_pause()
                    publish_event_fn("SPOTIFY_TOGGLE")
                    last_action = now

            # NEXT
            if is_hover(index_pos, POS_NEXT):
                if now - last_action > HOVER_DELAY:
                    skip_next()
                    publish_event_fn("SPOTIFY_NEXT")
                    last_action = now

            # HOME
            if is_hover(index_pos, POS_HOME):
                publish_event_fn("SPOTIFY_HOME")
                return

        pygame.display.flip()
        clock.tick(60)
