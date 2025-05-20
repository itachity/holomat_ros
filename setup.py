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
      'opencv-python',
      'mediapipe',
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
        ],
    },
)
