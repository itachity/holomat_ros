# holomat\_ros

A ROS2 Python package that opens your webcam and displays real-time hand‑tracking landmarks using MediaPipe.

## License

This project is licensed under the **BSD‑3‑Clause** License. See [LICENSE](./LICENSE) for details.

---

## 1) Required Dependencies

Make sure you have the following installed:

* **ROS2** with Python API (`rclpy`)
* **OpenCV**
* **MediaPipe**
* **PyYAML** (`pyyaml`)
* **setuptools** (for Python packaging)

---

## 2) Node List

Below are the ROS 2 nodes provided by this package:

| Node Name                | Description                                                  |
| ------------------------ | ------------------------------------------------------------ |
| **hand\_tracking\_node** | - Captures video from `/dev/video0`                          |
|                          | - Processes each frame using MediaPipe Hands (up to 2 hands) |
|                          | - Draws landmarks and hand‑connection lines on the frame     |
|                          | - Displays the annotated video in an OpenCV window           |
|                          | - Press **q** in the window (or Ctrl+C in terminal) to quit                          |

---

To run the node:

```bash
# Source your workspace and (if used) activate your venv
source ~/rob599/install/setup.bash
# or, with venv active:
# source ~/rob599/.venv/bin/activate && source ~/rob599/install/setup.bash

ros2 run holomat_ros hand_tracking_node
```

Enjoy real‑time hand tracking in ROS 2!
