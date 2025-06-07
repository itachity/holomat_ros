#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
"""
App 2 “Game” – invoked by ui_display_node when you hover‐select App 2.
"""

from holomat_ros.game_app import run as _game_run

def run(screen, camera_manager, publish_event_fn):
    """
    Run the Game application (Space Invaders → Brick Breaker).
    Delegates to holomat_ros.game_app.run(...)
    """
    _game_run(screen, camera_manager, publish_event_fn)
