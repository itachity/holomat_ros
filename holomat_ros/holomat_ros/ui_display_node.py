#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause

import os
import threading
import pygame
from pygame import mixer
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from holomat_ros.camera_manager import CameraManager
from holomat_ros.home_screen import run_home_screen
from apps.app_1 import app_1
from apps.app_2 import app_2
from apps.app_3 import app_3

class UIDisplayNode(Node):
    """
    Subscribes (implicitly via CameraManager) to fingertip TF frames.  
    Applies homography M.npy to get screen‐pixel coords.  
    Launches a fullscreen‐style Pygame UI on the _second_ monitor.  
    Publishes UI events on /ui_events.
    """

    def __init__(self):
        super().__init__("ui_display_node")
        self.get_logger().info("UIDisplayNode started")

        # Publisher for high‐level UI events
        self._ui_events_pub = self.create_publisher(String, "ui_events", 10)

        os.environ["SDL_VIDEODRIVER"] = "x11"
        os.environ["SDL_VIDEO_WINDOW_POS"] = "2560,0"           # origin of second display
        
        pygame.init()
        mixer.init()

        SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 757

        flags = pygame.NOFRAME | pygame.SWSURFACE
        self._screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            flags
        )
        self.get_logger().info("Launched borderless software window on second display")

        pygame.display.set_caption("Holomat UI (Display 2)")

        # Instantiate CameraManager
        homography_path = os.path.expanduser(
            '/home/itachity/rob599/src/holomat_ros/M.npy'
        )
        self._camera_manager = CameraManager(
            homography_path, SCREEN_WIDTH, SCREEN_HEIGHT, self
        )

        # Launch the UI loop in a background thread
        self._ui_thread = threading.Thread(
            target=self._run_ui, daemon=True
        )
        self._ui_thread.start()

    def _publish_ui_event(self, event_str: str):
        msg = String()
        msg.data = event_str
        self._ui_events_pub.publish(msg)
        self.get_logger().info(f"Published UI event: {event_str}")

    def _run_ui(self):
        try:
            run_home_screen(
                self._screen,
                self._camera_manager,
                self._publish_ui_event
            )
        except Exception as e:
            self.get_logger().error(f"UI loop crashed: {e}")
        finally:
            rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    node = UIDisplayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        pygame.quit()

if __name__ == "__main__":
    main()
