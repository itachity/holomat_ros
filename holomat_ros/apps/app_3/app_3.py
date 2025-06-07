#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
"""
App 3 “Spotify” – invoked by ui_display_node when you hover‐select App 3.
"""

from holomat_ros.spotify_app import run as _spotify_run

def run(screen, camera_manager, publish_event_fn):
    """
    Run the Spotify controller.
    Delegates to holomat_ros.spotify_app.run(...)
    """
    _spotify_run(screen, camera_manager, publish_event_fn)
