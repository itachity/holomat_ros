# holomat_ros

A ROS 2 Python package that captures your webcam feed, performs real-time hand‑tracking using MediaPipe, and provides a holistic interface for calibration and voice‑command interactions with an OpenAI-powered assistant.

- **hand_tracking_node**  
  • Captures webcam images, detects hand landmarks, broadcasts fingertip TFs, publishes fingertip markers, and republishes an annotated image topic.  
- **calibration_node**  
  • Uses fingertip TFs from `hand_tracking_node` to compute and save a homography for projecting fingertip positions onto a second display.  
  • Offers `/calibrate` and `/project_markers` services to run the calibration flow and project warped fingertip circles.  
- **voice_command_node**  
  • Combines an Action Server and Action Client in one node.  
  • Listens for the hot‑word “Jarvis” (via streaming STT) or direct text queries (`/jarvis_text_query`), forwards them to an OpenAI assistant thread, and returns spoken responses via TTS.  
  • Publishes any “#COMMAND” suffix from the AI’s response on `/jarvis_command_output`.
- A **UI** driven by fingertip hover (home screen + 3 apps)  
- **UI events** on `/ui_events` (e.g. `APP_LAUNCHED:2`) 

---

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
  libgtk-3-dev \
  python3-pip
```
Next, use pip3 (with --break-system-packages if prompted) to install the remaining Python dependencies:
```bash
# MediaPipe 
sudo pip3 install --break-system-packages mediapipe

# Real‑time STT, OpenAI SDK, Pygame, etc.
sudo pip3 install --break-system-packages \
  openai \
  pygame \
  RealtimeSTT \
  torch \
  torchvision \
  torchaudio
```
---

## 2) Node List & Topics


| Node Name                | Interfaces                                                                                                                                                                                                                                                                                                                                           | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **hand\_tracking\_node** | **Exec:**<br>`ros2 run holomat_ros hand_tracking_node`<br><br>**Publishes:**<br>• `/camera/image_raw` (`sensor_msgs/Image`)<br>• `/tf` (`TransformStamped`) named `hand<hand_idx>_finger<landmark_idx>` under `camera_frame`<br>• `/hand_markers` (`visualization_msgs/MarkerArray`)                                                                 | • Grabs video from `/dev/video0` at 640×480 (flipped horizontally).<br>• Uses MediaPipe Hands to detect up to 1 hand per frame (downsampled to 320×240 for speed).<br>• Broadcasts five fingertip TF frames (thumb – pinky) under `camera_frame` as `<child_frame_id>=hand{hand_index}_finger{landmark_idx}`.<br>• Publishes a red sphere (`MarkerArray`) at each fingertip in normalized (x,y) + z coordinates.<br>• Republishes the annotated BGR image on `/camera/image_raw`.<br>• (Optional: un-comment `cv2.imshow()` / `cv2.waitKey()` lines to display locally.)<br>• Quit by pressing **q** in the OpenCV window or with **Ctrl+C**.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **calibration\_node**    | **Exec:**<br>`ros2 run holomat_ros calibration_node`<br><br>**Services:**<br>• `/calibrate` (`holomat_interface/srv/Calibrate`)<br>  – Request: `{}`<br>  – Response: `{ success: bool }`<br>• `/project_markers` (`holomat_interface/srv/ProjectMarkers`)<br>  – Request: `{ enable: bool }`<br>  – Response: `{ success: bool }`                   | • **/calibrate**: Waits for the first `/camera/image_raw` frame. Then, in a fullscreen window on the second monitor (monitor 2), displays a 5×5 red‐circle grid (with 10% margins from left/right and 20% margins from top/bottom).<br>  – On **Enter**, captures the current index finger TF (`hand0_finger8`) and converts it from normalized (0–1) → pixel (x,y).<br>  – Repeats for all 25 grid points, computes a homography (`cv2.findHomography`) from camera pixels → projector pixels, and saves it as `M.npy` (default path: `~/rob599/src/holomat_ros/M.npy`).<br>  – Returns `{ success: true }` on success.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|                          |                                                                                                                                                                                                                                                                                                                                                      |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
|                          |                                                                                                                                                                                                                                                                                                                                                      |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **voice\_command\_node** | **Exec:**<br>`ros2 run holomat_ros voice_command_node`<br><br>**Subscriptions:**<br>• `/jarvis_text_query` (`std_msgs/String`) – deprecated if microphone is working; use only to send a single text query.<br><br>**Publishes:**<br>• `/jarvis_command_output` (`std_msgs/String`) – any “#COMMAND” suffix extracted from the assistant’s response. | • Runs both an Action Server *and* Action Client under the single node name `voice_command_node`.<br>• **Action Server** on `/jarvis_command` (`holomat_interface/action/JarvisCommand`): receives `{ query: string }` goals, forwards the query to an OpenAI “assistant thread” (using `ASSISTANT_ID` + `THREAD_ID`), waits for completion, and returns `{ response: string }`.<br>  – The last message in the assistant thread is treated as the “assistant’s reply.”<br>  – Any “#” in the reply splits it into a spoken portion (sent to TTS) and a `#COMMAND` portion (published on `/jarvis_command_output`).<br>• **STT loop (Action Client)**: continuously streams audio from your microphone (`RealtimeSTT.AudioToTextRecorder`), listens for the hot‑word “Jarvis.” When detected, strips “Jarvis,” sends the remainder as a `/jarvis_command` goal to *itself*, and waits for result.<br>  – Uses `pygame.mixer` to play back the TTS‑generated MP3 file, then restarts STT.<br>• **Text‐mode fallback**: if the mic/STT isn’t working, publish a single‐message `std_msgs/String` on `/jarvis_text_query` (e.g. using `ros2 topic pub --once`) to immediately forward it as a `/jarvis_command` goal.<br>• Quit with **Ctrl+C**. |                                                           |
| **ui\_display\_node**    | **Exec:**<br>`ros2 run holomat_ros ui_display_node`<br><br>**Publishes:**<br>• `/ui_events` (std\_msgs/String) high-level UI signals (e.g. `APP_LAUNCHED:2`, `HOME_TOGGLED`)                                                                                 | Uses `camera_manager` + homography to map fingertip TFs → screen coords, runs a fullscreen Pygame “home screen” with **3** app icons.  Hover selections launch the respective `apps/app_n/app_n.py`.  Emits UI events over ROS. |


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
ros2 topic pub /jarvis_text_query std_msgs/msg/String "{ data: 'Tell me a joke' }" --once

# UI_display_node
ros2 run holomat_ros ui_display_node

# Launch File (hand_tracking_node -> ui_display_node -> rviz2)
ros2 launch holomat_ros holomat_ui_launch.py
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

[![Demo Video](https://img.youtube.com/vi/-vL0-piHwcM/0.jpg)](https://youtu.be/-vL0-piHwcM)


