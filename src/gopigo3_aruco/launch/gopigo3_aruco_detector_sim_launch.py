from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='aruco_opencv',
            executable='aruco_tracker_autostart',
            name='aruco_tracker',
            namespace='robot_1',
            output='screen',
            parameters=[
                {'cam_base_topic': '/robot_1/camera/image_raw'},
                {'marker_size': 0.15},
            ]
        ),
        Node(
            package='aruco_opencv',
            executable='aruco_tracker_autostart',
            name='aruco_tracker',
            namespace='robot_2',
            output='screen',
            parameters=[
                {'cam_base_topic': '/robot_2/camera/image_raw'},
                {'marker_size': 0.15},
            ]
        ),
    ])