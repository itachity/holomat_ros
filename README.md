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


| Node Name                | Interfaces                                                                                                                                                                                                                                                                                                                       | Description                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **hand\_tracking\_node** | **Exec:**<br>`ros2 run holomat_ros hand_tracking_node`<br><br>**Publishes:**<br>• `/camera/image_raw` (sensor\_msgs/Image)<br>• `/tf` (TransformStamped) named `hand<hand_idx>_finger<landmark_idx>` under `camera_frame`<br>• `/hand_markers` (visualization\_msgs/MarkerArray)                                                 | • Captures video from `/dev/video0`<br>• Runs MediaPipe Hands to detect up to 2 hands<br>• Broadcasts fingertip TFs<br>• Publishes spherical markers at each fingertip<br>• Displays annotated feed in an OpenCV window<br>• Quit with **q** in the window or **Ctrl+C**                                                                                                                                      |
| **calibration\_node**    | **Exec:**<br>`ros2 run holomat_ros calibration_node`<br><br>**Services:**<br>• `/calibrate` (holomat\_interface/srv/Calibrate)<br>  – Request: `{}`<br>  – Response: `{ success: bool }`<br>• `/project_markers` (holomat\_interface/srv/ProjectMarkers)<br>  – Request: `{ enable: bool }`<br>  – Response: `{ success: bool }` | • `/calibrate`: waits for first camera frame, shows a fullscreen 9‑point grid on monitor 2, records fingertip TFs on **Enter**, computes & saves homography `M.npy` under `~/.ros/`<br>• `/project_markers`: with `enable:true` opens a fullscreen window on monitor 2 and continuously warps & draws green circles at all five fingertip TFs until you press **q**; with `enable:false` returns immediately. |

---

## 3) Running the Node

```bash
#On your workspace
colcon build --packages-select holomat_ros holomat_interface
source install/setup.bash

# Run the hand tracking node:
ros2 run holomat_ros hand_tracking_node
ros2 run holomat_ros calibration_node

# Service Calls
ros2 service call /calibrate holomat_interface/srv/Calibrate "{}"
ros2 service call /project_markers holomat_interface/srv/ProjectMarkers "{ enable: true }"
ros2 service call /project_markers holomat_interface/srv/ProjectMarkers "{ enable: false }"

# Voice Command
ros2 run holomat_ros voice_command_server
ros2 run holomat_ros voice_command_node
# if mic is not working
ros2 topic pub /jarvis_text_query std_msgs/msg/String "{ data: 'What should i do today?' }" --once
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

Watch a recorded demo of the hand_tracking_node running with RViz2:

![Hand Tracking with RViz2](./recordings/hand_tracking_withrviz2.webm)
