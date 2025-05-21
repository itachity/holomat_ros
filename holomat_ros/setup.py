from setuptools import find_packages, setup

package_name = 'holomat_ros'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=[
      'setuptools',
      'rclpy',
      'rclpy_action',
      'opencv-python',
      'mediapipe',
      'tf2_ros',
      'geometry_msgs',
      'visualization_msgs',
      'cv_bridge',
      'sensor_msgs',
      'holomat_interface',
      'numpy',
    ],
    zip_safe=True,
    maintainer='MJ Santos',
    maintainer_email='santosmatthewjohn@gmail.com',
    description='Holomat Project on Ros',
    license='BSD-3-Clause',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'hand_tracking_node = holomat_ros.hand_tracking_node:main',
            'calibration_node = holomat_ros.calibration_node:main',
            'projection_action = holomat_ros.calibration_node:main',
        ],
    },
)
