#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause

import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
from visualization_msgs.msg import Marker, MarkerArray
from cv_bridge import CvBridge
from sensor_msgs.msg import Image

import cv2
import mediapipe as mp


class HandTrackingNode(Node):
    def __init__(self):
        super().__init__('hand_tracking_node')
        self.get_logger().info('Initializing MediaPipe Hands + TF, Marker & Image publishers...')

        # MediaPipe setup
        mp_hands = mp.solutions.hands
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.1,
            min_tracking_confidence=0.1
        )
        self.drawing_utils = mp.solutions.drawing_utils
        self.hand_connections = mp_hands.HAND_CONNECTIONS

        # TF broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)
        # Marker publisher
        self.marker_pub = self.create_publisher(MarkerArray, 'hand_markers', 10)
        # Image publisher
        self.bridge = CvBridge()
        self.image_pub = self.create_publisher(Image, 'camera/image_raw', 10)

        # OpenCV camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.get_logger().error('Cannot open camera')
            raise RuntimeError('Camera not available')

        # force lower resolution (faster processing)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def run(self):
        self.get_logger().info('Starting hand tracking loop. Press "q" to quit.')
        while rclpy.ok():
            ret, frame = self.cap.read()
            if not ret:
                self.get_logger().warn('Empty frame, skipping...')
                continue

            frame = cv2.flip(frame, 1)
            #rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            #results = self.hands.process(rgb)

            # downsize
            small = cv2.resize(frame, (320, 240))
            rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_small)

            now = self.get_clock().now().to_msg()
            markers = MarkerArray()

            if results.multi_hand_landmarks:
                for hand_index, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    # Broadcast TF and create markers for each fingertip
                    frame_h, frame_w = frame.shape[:2]
                    for idx in [4, 8, 12, 16, 20]:  # thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip
                        lm = hand_landmarks.landmark[idx]

                        # normalized coords from 320×240 → scale to 640×480
                        x_pix = lm.x * frame_w
                        y_pix = lm.y * frame_h
                        z_norm = lm.z    

                        # TF frame
                        tf = TransformStamped()
                        tf.header.stamp = now
                        tf.header.frame_id = 'camera_frame'
                        tf.child_frame_id = f'hand{hand_index}_finger{idx}'
                        tf.transform.translation.x = lm.x
                        tf.transform.translation.y = lm.y
                        tf.transform.translation.z = lm.z
                        tf.transform.rotation.x = 0.0
                        tf.transform.rotation.y = 0.0
                        tf.transform.rotation.z = 0.0
                        tf.transform.rotation.w = 1.0
                        self.tf_broadcaster.sendTransform(tf)

                        # Marker
                        marker = Marker()
                        marker.header.stamp = now
                        marker.header.frame_id = 'camera_frame'
                        marker.ns = f'hand{hand_index}'
                        marker.id = idx
                        marker.type = Marker.SPHERE
                        marker.action = Marker.ADD
                        marker.pose.position.x = x_pix / 640.0
                        marker.pose.position.y = y_pix / 480.0
                        marker.pose.position.z = z_norm
                        marker.pose.orientation.x = 0.0
                        marker.pose.orientation.y = 0.0
                        marker.pose.orientation.z = 0.0
                        marker.pose.orientation.w = 1.0
                        marker.scale.x = 0.05
                        marker.scale.y = 0.05
                        marker.scale.z = 0.05
                        marker.color.r = 1.0
                        marker.color.g = 0.0
                        marker.color.b = 0.0
                        marker.color.a = 0.8
                        markers.markers.append(marker)

                    # Draw landmarks on the frame
                    self.drawing_utils.draw_landmarks(
                        frame, hand_landmarks, self.hand_connections
                    )

            # Publish markers
            self.marker_pub.publish(markers)

            # Publish image with landmarks
            img_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            img_msg.header.stamp = now
            img_msg.header.frame_id = 'camera_frame'
            self.image_pub.publish(img_msg)

            # Display locally
            #cv2.imshow('Hand Tracking', frame)
            #if cv2.waitKey(1) & 0xFF == ord('q'):
            #    break

        self.cap.release()
        cv2.destroyAllWindows()


def main(args=None):
    rclpy.init(args=args)
    node = HandTrackingNode()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
