#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause

import os
import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.time import Time

from holomat_interface.srv import Calibrate, ProjectMarkers
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from tf2_ros import Buffer, TransformListener

# --- Configuration -----------------------------------------------------------

# Where to save your homography, change as needed
HOMOGRAPHY_FILE = os.path.expanduser('/home/itachity/rob599/src/holomat_ros/M.npy')

# Projector resolution (second display)
PROJ_W, PROJ_H = 1600, 757

# Offset to move windows onto the projector
PRIMARY_DISPLAY_WIDTH = 2560  # adjust to your setup

# 5x5 target points for calibration
_NX = 5
_NY = 5
X_MARGIN = int(PROJ_W * 0.1)           # 10% from left/right
Y_MARGIN = int(PROJ_H * 0.2)           # 20% from top/bottom
usable_w = PROJ_W - 2 * X_MARGIN
usable_h = PROJ_H - 2 * Y_MARGIN

TARGET_POINTS = []
for row in range(_NY):
    y = Y_MARGIN + int(row * (usable_h / (_NY - 1)))
    for col in range(_NX):
        x = X_MARGIN + int(col * (usable_w / (_NX - 1)))
        TARGET_POINTS.append((x, y))
        
# Which fingertip to use for calibration and projection
FINGER_IDX = 8  # index finger tip

# ------------------------------------------------------------------------------

class CalibrationNode(Node):
    def __init__(self):
        super().__init__('calibration_node')
        self.get_logger().info('CalibrationNode started')

        # Subscribe to the annotated camera feed from hand_tracking_node
        self.bridge = CvBridge()
        self.latest_frame = None
        self.create_subscription(
            Image, 'camera/image_raw', self._image_cb, 1)

        # TF buffer + listener for fingertip frames
        self.tf_buffer   = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Service
        self.create_service(Calibrate, 'calibrate', self.handle_calibrate)
        self.create_service(ProjectMarkers, 'project_markers', self.handle_project)

    def _image_cb(self, msg: Image):
        """Store the last camera frame for preview."""
        try:
            self.latest_frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().warn(f'Could not convert image: {e}')

    def handle_calibrate(self, request, response):
        """
        /calibrate → capture 9 fingertip positions (via TF), compute homography,
        and save it to HOMOGRAPHY_FILE.
        """
        # Wait until we have at least one frame
        while rclpy.ok() and self.latest_frame is None:
            rclpy.spin_once(self, timeout_sec=0.1)

        frame_h, frame_w = self.latest_frame.shape[:2]
        calib_pts = []

        # Fullscreen target window on projector
        win = 'Calibration'
        cv2.namedWindow(win, cv2.WINDOW_FULLSCREEN)
        cv2.moveWindow(win, PRIMARY_DISPLAY_WIDTH, 0)

        for i, tgt in enumerate(TARGET_POINTS):
            while rclpy.ok():

                # let ROS process incoming TF and image messages
                rclpy.spin_once(self, timeout_sec=0.001)

                # Draw the red circle at projector coords
                canvas = np.zeros((PROJ_H, PROJ_W, 3), np.uint8)
                cv2.circle(canvas, tgt, 20, (0,0,255), -1)
                cv2.putText(canvas, f'Point {i+1}', (tgt[0]+25,tgt[1]-25),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
                cv2.imshow(win, canvas)

                key = cv2.waitKey(1)
                if key == 13:  # \r or Enter
                    try:
                        # Lookup the fingertip TF in normalized coords
                        tf = self.tf_buffer.lookup_transform(
                            'camera_frame',
                            f'hand0_finger{FINGER_IDX}',
                            Time())
                        nx = tf.transform.translation.x
                        ny = tf.transform.translation.y
                        # Convert normalized → pixel coords
                        x_cam = int(nx * frame_w)
                        y_cam = int(ny * frame_h)
                        calib_pts.append((x_cam, y_cam))
                        self.get_logger().info(
                            f'Captured {i+1}: pixel=({x_cam},{y_cam})')
                        break
                    except Exception as e:
                        self.get_logger().warn(f'TF lookup failed: {e}')
                        continue

        cv2.destroyWindow(win)

        # Compute homography (RANSAC for robustness)
        pts_cam = np.array(calib_pts, np.float32)
        pts_tgt = np.array(TARGET_POINTS, np.float32)
        H, _ = cv2.findHomography(pts_cam, pts_tgt, cv2.RANSAC)

        # Save
        os.makedirs(os.path.dirname(HOMOGRAPHY_FILE), exist_ok=True)
        np.save(HOMOGRAPHY_FILE, H)
        self.get_logger().info(f'Homography saved at {HOMOGRAPHY_FILE}')

        response.success = True
        return response

    def handle_project(self, request, response):
        """
        /project_markers → enable=True will open a fullscreen projector window
        and continuously draw warped fingertip circles until you press 'q'.
        """
        self.get_logger().info(f"[handle_project] called with enable={request.enable}")

        # If called with enable=False, do nothing
        if not request.enable:
            self.get_logger().info("[handle_project] projection disabled by request")
            response.success = True
            return response

        # Load the homography
        if not os.path.exists(HOMOGRAPHY_FILE):
            self.get_logger().error("[handle_project] calibration file not found")
            response.success = False
            return response
        H = np.load(HOMOGRAPHY_FILE)
        self.get_logger().info(f"[handle_project] loaded homography shape={H.shape}")

        # Open a true fullscreen window on monitor 2
        win = 'Projection'
        cv2.namedWindow(win, cv2.WINDOW_FULLSCREEN)
        cv2.moveWindow(win, PRIMARY_DISPLAY_WIDTH, 0)
        self.get_logger().info(f"[handle_project] window '{win}' fullscreen on x={PRIMARY_DISPLAY_WIDTH}")

        finger_ids = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky tips

        # Main loop: until you hit 'q'
        while rclpy.ok():
            # pump TF & image subscriptions
            rclpy.spin_once(self, timeout_sec=0.01)

            if self.latest_frame is None:
                self.get_logger().debug("[handle_project] waiting for first image...")
                continue

            fh, fw = self.latest_frame.shape[:2]
            canvas = np.zeros((PROJ_H, PROJ_W, 3), dtype=np.uint8)
            projected = []

            for idx in finger_ids:
                try:
                    # get the latest transform (Time() -> most recent)
                    tf = self.tf_buffer.lookup_transform(
                        'camera_frame',
                        f'hand0_finger{idx}',
                        Time()
                    )
                    nx = tf.transform.translation.x
                    ny = tf.transform.translation.y

                    # turn normalized coords to pixel
                    cam_pt = np.array([[[nx * fw, ny * fh]]], dtype=np.float32)
                    warped = cv2.perspectiveTransform(cam_pt, H)[0][0]
                    x_p, y_p = int(warped[0]), int(warped[1])

                    if 0 <= x_p < PROJ_W and 0 <= y_p < PROJ_H:
                        # draw and record
                        cv2.circle(canvas, (x_p, y_p), 10, (0,255,0), -1)
                        projected.append((idx, x_p, y_p))
                except Exception as e:
                    self.get_logger().debug(f"[handle_project] idx={idx} lookup/warp failed: {e}")
                    continue

            if projected:
                self.get_logger().info(f"[handle_project] projected: {projected}")
            else:
                self.get_logger().warn("[handle_project] no fingertips projected this frame")

            cv2.imshow(win, canvas)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.get_logger().info("[handle_project] quit key pressed, closing")
                break

        cv2.destroyWindow(win)
        response.success = True
        return response



def main(args=None):
    rclpy.init(args=args)
    node = CalibrationNode()
    
    rclpy.spin(node)
        
    cv2.destroyAllWindows()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
