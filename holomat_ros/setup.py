from setuptools import find_packages, setup
import os
from glob import glob


package_name = 'holomat_ros'

# collect all data files under a directory
def package_files(directory, extensions):
    paths = []
    for (path, _, filenames) in os.walk(os.path.join(package_name, directory)):
        for f in filenames:
            if any(f.endswith(ext) for ext in extensions):
                relative_path = os.path.join(path, f)
                paths.append(os.path.relpath(relative_path, package_name))
    return paths

app_images = package_files('apps', ['.py', '.jpg', '.png'])
audio_files = package_files('audio', ['.wav', '.mp3'])

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.py'))),
        ('share/' + package_name + '/apps', [os.path.join(package_name, p) for p in app_images]),
        ('share/' + package_name + '/audio', [os.path.join(package_name, p) for p in audio_files]),
    ],
    install_requires=[
        'setuptools',
        'numpy',
        'opencv-python',
        'mediapipe',
        'openai',
        'pygame',
        'RealtimeSTT',
    ],
    zip_safe=True,
    maintainer='MJ Santos',
    maintainer_email='santosmatthewjohn@gmail.com',
    description='Holomat Project on ROS2: hand tracking, calibration, and voice control',
    license='BSD-3-Clause',
    entry_points={
        'console_scripts': [
            'hand_tracking_node = holomat_ros.hand_tracking_node:main',
            'calibration_node = holomat_ros.calibration_node:main',
            'voice_command_node = holomat_ros.voice_command_node:main',
            'ui_display_node  = holomat_ros.ui_display_node:main',
        ],
    },
)
