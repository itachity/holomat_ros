#!/usr/bin/env python3
# home_screen.py

import os
import time
import math
import pygame
from pygame import mixer
from ament_index_python.packages import get_package_share_directory

# find holomat_ros/share/holomat_ros
PKG_SHARE = get_package_share_directory('holomat_ros')
APPS_DIR  = os.path.join(PKG_SHARE, 'apps')
AUDIO_DIR = os.path.join(PKG_SHARE, 'audio')

def run_home_screen(screen, camera_manager, publish_event_fn):
    """
    screen           : the Pygame display surface (fullscreen)
    camera_manager   : instance of CameraManager
    publish_event_fn : function(str) to call whenever a UI event occurs

    This version displays:
      - one central “Home” circle
      - three evenly spaced “App” circles around it
    """
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    NAVY_BLUE    = (20, 20, 40)
    LIGHT_BLUE   = (173, 216, 230)
    HOME_TOGGLE_DELAY = 2.0
    APP_SELECT_DELAY  = 2.0

    class AppCircle:
        def __init__(self, center, radius, app_index, final_pos, is_main=False):
            self.center          = center
            self.radius          = radius
            self.app_index       = app_index
            self.is_main         = is_main
            self.visible         = is_main
            self.final_pos       = final_pos
            self.hover_start     = None
            self.animation_start = None
            self.image           = self._load_image()

        def _load_image(self):
            if not self.is_main:
                # look under share/holomat_ros/apps/app_N/icon.jpg
                path = os.path.join(APPS_DIR,
                                    f'app_{self.app_index}',
                                    'icon.jpg')
                if os.path.exists(path):
                    img = pygame.image.load(path)
                    return pygame.transform.scale(img, (2*self.radius, 2*self.radius))
            return None

        def draw(self, screen):
            # hover-scale
            if self.hover_start:
                elapsed = time.time() - self.hover_start
                cur_r = self.radius + min(elapsed*10, self.radius*0.5)
            else:
                cur_r = self.radius

            # animate in/out from center
            if self.animation_start:
                t = (time.time() - self.animation_start) / 0.5
                if t < 1.0:
                    cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
                    fx, fy = self.final_pos
                    if self.visible:
                        x = (1-t)*cx + t*fx
                        y = (1-t)*cy + t*fy
                    else:
                        x = t*cx + (1-t)*fx
                        y = t*cy + (1-t)*fy
                    self.center = (int(x), int(y))
                else:
                    self.center = self.final_pos if self.visible else (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
                    self.animation_start = None

            # only draw if visible or animating
            if self.visible or self.animation_start:
                if self.image:
                    tl = (self.center[0]-self.radius, self.center[1]-self.radius)
                    screen.blit(self.image, tl)
                else:
                    pygame.draw.circle(screen, NAVY_BLUE, self.center, int(cur_r))
                pygame.draw.circle(screen, LIGHT_BLUE, self.center, int(cur_r), 5)

                if not self.image:
                    font = pygame.font.Font(None, 32)
                    label = 'Home' if self.is_main else f'App {self.app_index}'
                    surf  = font.render(label, True, (255,255,255))
                    rect  = surf.get_rect(center=self.center)
                    screen.blit(surf, rect)

        def is_hovered(self, pos):
            if not self.visible:
                return False
            dx = pos[0] - self.center[0]
            dy = pos[1] - self.center[1]
            return dx*dx + dy*dy <= self.radius*self.radius


    def create_circles():
        circles = []
        cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
        main_r = 100
        app_r  = 75
        dist   = 250
        # central Home
        circles.append(AppCircle((cx,cy), main_r, 0, (cx,cy), is_main=True))

        # three apps at 0°, 120°, 240°
        for i in range(3):
            angle = math.radians(i * 120)
            x = cx + int(dist * math.cos(angle))
            y = cy + int(dist * math.sin(angle))
            circles.append(AppCircle((cx,cy), app_r, i+1, (x,y)))

        return circles

    # initialize
    circles         = create_circles()
    main_circle     = circles[0]
    apps_visible    = False
    last_toggle     = 0
    last_app_select = 0
    index_pos       = None

    # optional startup sound
    audio_start = os.path.join('audio','startup.wav')
    if os.path.exists(audio_start):
        mixer.music.load(audio_start)
        mixer.music.play()

    running = True
    while running:
        camera_manager.update()              # grab new TFs & landmarks

        for ev in pygame.event.get():        # handle exit
            if ev.type == pygame.QUIT:
                running = False
            if ev.type == pygame.KEYDOWN and ev.key==pygame.K_ESCAPE:
                running = False

        screen.fill((0,0,0))

        for c in circles:
            c.draw(screen)

        # draw finger cursor
        hands = camera_manager.get_transformed_landmarks()
        if hands:
            hand0 = hands[0]
            if hand0[8]:
                index_pos = hand0[8]
                pygame.draw.circle(screen, LIGHT_BLUE, index_pos, 15, 3)

        # hover logic
        if index_pos:
            now = time.time()
            for c in circles:
                if c.is_hovered(index_pos):
                    if c.hover_start is None:
                        c.hover_start = now

                    # HOME toggle
                    if c.is_main:
                        if now - c.hover_start >= HOME_TOGGLE_DELAY:
                            apps_visible = not apps_visible
                            last_toggle = now
                            for a in circles[1:]:
                                a.visible         = apps_visible
                                a.animation_start = now
                            publish_event_fn("HOME_TOGGLED")
                            c.hover_start = None

                    # APP launch
                    else:
                        if c.visible and apps_visible and (now >= last_app_select):
                            if now - c.hover_start >= APP_SELECT_DELAY:
                                publish_event_fn(f"APP_LAUNCHED:{c.app_index}")
                                try:
                                    mod = __import__(
                                        f"apps.app_{c.app_index}.app_{c.app_index}",
                                        fromlist=['run']
                                    )
                                    mod.run(screen, camera_manager, publish_event_fn)
                                except ModuleNotFoundError:
                                    print(f"apps.app_{c.app_index} not found")
                                # reset back to home
                                for a in circles[1:]:
                                    a.visible = False
                                    a.center  = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
                                c.hover_start = None
                    break

                else:
                    c.hover_start = None

        pygame.display.flip()
        pygame.time.delay(50)

    pygame.quit()
