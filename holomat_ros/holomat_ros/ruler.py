# ruler.py
import pygame
import math
import time
from pygame import mixer

def run(screen, camera_manager, publish_event_fn):
    """
    A simple “ruler” app:
      - Pinch (thumb+index < 50px) to start drawing a line,
      - Release pinch to fix that line and measure distance in mm,
      - Hover the Home button (in top‐left) to return to home screen.
    """
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    BACKGROUND = (0,0,0)
    LINE_COLOR = (173,216,230)  # Light Blue
    TEXT_COLOR = (255,255,255)
    HOME_CENTER = (150, 100)
    HOME_RADIUS = 50
    PINCH_THRESHOLD = 60
    PINCH_HOLD_TIME = 0.2
    PIXEL_TO_MM = 0.4478

    def distance(p1, p2):
        return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

    start_pt = None
    end_pt = None
    drawing = False
    pinch_start = 0
    lines = []

    if os.path.exists("./audio/startup.wav"):
        mixer.music.load("./audio/startup.wav")
        mixer.music.play()

    clock = pygame.time.Clock()
    running = True
    while running:
        camera_manager.update()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
                break
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                running = False
                break

        screen.fill(BACKGROUND)

        hands = camera_manager.get_transformed_landmarks()
        if hands:
            hand0 = hands[0]
            pos_thumb = hand0[4]  # (x_px,y_px) or None
            pos_index = hand0[8]
            if pos_thumb and pos_index:
                mid = ((pos_thumb[0]+pos_index[0])//2, (pos_thumb[1]+pos_index[1])//2)
                d = distance(pos_thumb, pos_index)
                pygame.draw.circle(screen, LINE_COLOR, mid, 10, 3)

                if d < PINCH_THRESHOLD:
                    # Pinch started
                    if not drawing:
                        drawing = True
                        start_pt = mid
                        pinch_start = time.time()
                        if os.path.exists("./audio/drawing.wav"):
                            mixer.music.load("./audio/drawing.wav")
                            mixer.music.play()
                    else:
                        end_pt = mid
                else:
                    # Pinch released
                    if drawing and end_pt:
                        lines.append((start_pt, end_pt))
                        if os.path.exists("./audio/quick_click.wav"):
                            mixer.music.load("./audio/quick_click.wav")
                            mixer.music.play()
                    drawing = False

        # Draw permanent lines + measure
        font = pygame.font.Font(None, 36)
        for (p0, p1) in lines:
            pygame.draw.line(screen, LINE_COLOR, p0, p1, 2)
            l_mm = distance(p0,p1) * PIXEL_TO_MM
            midpt = ((p0[0]+p1[0])//2, (p0[1]+p1[1])//2)
            txt = font.render(f"{l_mm:.2f} mm", True, TEXT_COLOR)
            screen.blit(txt, midpt)

        # If currently drawing
        if drawing and start_pt and end_pt:
            pygame.draw.line(screen, LINE_COLOR, start_pt, end_pt, 2)
            l_mm = distance(start_pt,end_pt) * PIXEL_TO_MM
            midpt = ((start_pt[0]+end_pt[0])//2, (start_pt[1]+end_pt[1])//2)
            txt = font.render(f"{l_mm:.2f} mm", True, TEXT_COLOR)
            screen.blit(txt, midpt)

        # Check hover over home button
        if hands and hand0[8]:
            if distance(hand0[8], HOME_CENTER) <= HOME_RADIUS:
                publish_event_fn("RULER_HOME_PRESSED")
                running = False

        # Draw home UI
        pygame.draw.circle(screen, (20,20,40), HOME_CENTER, HOME_RADIUS)
        pygame.draw.circle(screen, (173,216,230), HOME_CENTER, HOME_RADIUS, 5)
        home_txt = font.render("Home", True, TEXT_COLOR)
        home_rect = home_txt.get_rect(center=HOME_CENTER)
        screen.blit(home_txt, home_rect)

        pygame.display.flip()
        clock.tick(60)

    # Exiting Ruler → Back to home_screen
    return
