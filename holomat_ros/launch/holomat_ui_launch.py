#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    return LaunchDescription([
        # 1) hand_tracking_node
        Node(
            package='holomat_ros',
            executable='hand_tracking_node',
            name='hand_tracking_node',
            output='screen',
            parameters=[{
                # any params if you want
            }]
        ),

        # 2) ui_display_node
        Node(
            package='holomat_ros',
            executable='ui_display_node',
            name='ui_display_node',
            output='screen',
        ),

        # 3) RViz2
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
        ),
    ])
