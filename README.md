# holomat_ros

A ROS 2 Python package that captures your webcam feed, performs real-time hand‑tracking using MediaPipe, and publishes:

- **TF frames** for each fingertip under `camera_frame`
- **MarkerArray** messages to visualize fingertip spheres in RViz2
- **sensor_msgs/Image** topic for the annotated camera image

## License

This project is licensed under the **BSD‑3‑Clause** License. See [LICENSE](./LICENSE) for details.

---

## 1) Required Dependencies

Install the following packages for ROS 2 **Jazzy** on Ubuntu:

```bash
sudo apt update
sudo apt install \
  ros-jazzy-rclpy \
  ros-jazzy-tf2-ros \
  ros-jazzy-geometry-msgs \
  ros-jazzy-visualization-msgs \
  ros-jazzy-cv-bridge \
  ros-jazzy-sensor-msgs \
  python3-opencv \
  libgtk-3-dev
```
---

## 2) Node List & Topics

| Node Name             | Topics Published                       | Description                                                                                  |
| --------------------- | ---------------------------------------| -------------------------------------------------------------------------------------------- |
| **hand_tracking_node** | `/camera/image_raw` (sensor_msgs/Image)  | - Captures video from `/dev/video0`                                                          |
|                       | `/tf` (TransformStamped)               | - Broadcasts TF frames at `hand<idx>_finger<id>` under `camera_frame`                         |
|                       | `/hand_markers` (visualization_msgs)    | - Publishes MarkerArray spheres (2 cm) at each fingertip                                      |
|                       |                                         | - Displays annotated feed in OpenCV window                                                   |
|                       |                                         | - Quit with **q** in window or **Ctrl+C**                                                     |

---

## 3) Running the Node

```bash
source ~/rob599/install/setup.bash

# Run the hand tracking node:
ros2 run holomat_ros hand_tracking_node
```

---

## 4) Visualizing in RViz2

1. **Start RViz2**:
   ```bash
   rviz2
   ```
2. **Set Fixed Frame** to `camera_frame`.  
3. **Add Displays**:
   - **Image** → Topic: `/camera/image_raw`  
   - (Optional) **TF** → to view fingertip frames  
   - **Marker** → Topic: `/hand_markers`  

You will see the camera feed with landmarks, (the 3D axes of fingertip frames), and red spheres at each fingertip in the RViz viewport.

---

## 5) Demonstration

Watch a recorded demo of the node running with RViz2:

![Hand Tracking with RViz2](./recordings/hand_tracking_withrviz2.webm)
