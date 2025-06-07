# camera_manager.py
import os
import cv2
import numpy as np
import rclpy
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener

class CameraManager:
    """
    - Loads homography M.npy (camera 640×480 → UI screen).
    - Uses tf2_ros to look up fingertip transforms under 'camera_frame'.
    - Applies homography to get UI‐pixel (x,y) for each fingertip.
    - Stores a list of "hand landmarks".
    """

    def __init__(self, homography_path: str, screen_w: int, screen_h: int, node: rclpy.node.Node):
        if not os.path.exists(homography_path):
            raise FileNotFoundError(f"camera_manager: cannot find homography: {homography_path}")
        self._H = np.load(homography_path)
        self._screen_w = screen_w
        self._screen_h = screen_h
        self._node = node

        # Set up tf2 listener to receive fingertip transforms
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, node)

        # We assume only one hand (hand0). We will fill in a list of length 21,
        # but we only actually get TFs for indices [4,8,12,16,20]. The rest remain None.
        self._latest_hand_landmarks = []  # List[List[ (x_px, y_px) or None ]]

        # Camera‐side resolution (hard‐coded to 640×480, same as hand_tracking_node)
        self._cam_w = 640
        self._cam_h = 480

    def update(self) -> bool:
        """
        1. Runs rclpy.spin_once(...) so tf buffer can update.
        2. Tries to look up each fingertip TF under "camera_frame" → "hand0_finger{idx}".
        3. Converts normalized (nx,ny) → camera‐pixel, then applies H → UI‐pixel.
        4. Stores a 21‐length list (None or (ui_x,ui_y)) at self._latest_hand_landmarks.
        Returns True if at least one fingertip was found this cycle, False otherwise.
        """
        # 1) Pump ROS so tf buffers get new data
        rclpy.spin_once(self._node, timeout_sec=0.005)

        finger_indices = [4, 8, 12, 16, 20]  # only these five landmarks are broadcast
        hand0_landmarks = [None] * 21  # placeholders for all 21 MediaPipe indices

        found_any = False

        for idx in finger_indices:
            frame_id = f"hand0_finger{idx}"
            try:
                tf_stamped = self._tf_buffer.lookup_transform(
                    "camera_frame", frame_id, Time())
                # normalized coords (0..1)
                nx = tf_stamped.transform.translation.x
                ny = tf_stamped.transform.translation.y

                # 2) Convert to camera pixels
                cam_x = nx * self._cam_w
                cam_y = ny * self._cam_h

                # 3) Apply homography → UI‐pixel
                pt_in = np.array([[[cam_x, cam_y]]], dtype=np.float32)  # shape=(1,1,2)
                pt_out = cv2.perspectiveTransform(pt_in, self._H)[0][0]
                ui_x = int(round(pt_out[0]))
                ui_y = int(round(pt_out[1]))

                # Optional: clamp to UI bounds
                ui_x = max(0, min(ui_x, self._screen_w - 1))
                ui_y = max(0, min(ui_y, self._screen_h - 1))

                hand0_landmarks[idx] = (ui_x, ui_y)
                found_any = True
            except Exception:
                # TF not yet available for this finger in this iteration
                continue

        # If we found at least one fingertip, store it; otherwise, clear
        if found_any:
            self._latest_hand_landmarks = [hand0_landmarks]
        else:
            self._latest_hand_landmarks = []
        return found_any

    def get_transformed_landmarks(self):
        """
        Returns a list of hands; each hand is a list of length 21,
        where each element is either (x_px, y_px) on the UI screen or None.
        Example:
          [
            [ None, None, ..., (123,456), ..., None ],  # 21 slots
          ]
        If no hand is visible, returns [].
        """
        return self._latest_hand_landmarks

    def release(self):
        """
        If you ever need to clean up or disable tf listener, do it here.
        (Currently no special teardown needed.)
        """
        pass
