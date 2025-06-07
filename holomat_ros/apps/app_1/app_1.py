#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
"""
App 1 “Ruler” – invoked by ui_display_node when you hover‐select App 1.
"""

from holomat_ros.ruler import run as _ruler_run

def run(screen, camera_manager, publish_event_fn):
    """
    Run the Ruler application.
    Delegates to holomat_ros.ruler.run(...)
    """
    _ruler_run(screen, camera_manager, publish_event_fn)
