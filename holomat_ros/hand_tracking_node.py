#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause

import rclpy
from rclpy.node import Node

import cv2
import mediapipe as mp


class HandTrackingNode(Node):
    def __init__(self):
        super().__init__('hand_tracking_node')
        self.get_logger().info('Initializing MediaPipe Hands...')
        mp_hands = mp.solutions.hands
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.1,
            min_tracking_confidence=0.1)
        self.drawing_utils = mp.solutions.drawing_utils
        self.hand_connections = mp_hands.HAND_CONNECTIONS

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.get_logger().error('Cannot open camera')
            rclpy.shutdown()

    def run(self):
        self.get_logger().info('Starting hand tracking loop. Press "q" to quit.')
        while rclpy.ok():
            ret, frame = self.cap.read()
            if not ret:
                self.get_logger().warn('Empty frame, skipping...')
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            if results.multi_hand_landmarks:
                for landmarks in results.multi_hand_landmarks:
                    self.drawing_utils.draw_landmarks(
                        frame, landmarks, self.hand_connections)

            # Optional: resize for full‑HD display
            frame = cv2.resize(frame, (1920, 1080))
            cv2.imshow('Hand Tracking', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()


def main(args=None):
    rclpy.init(args=args)
    node = HandTrackingNode()
    try:
        node.run()                  # <-- drives your OpenCV loop
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()



if __name__ == '__main__':
    main()
