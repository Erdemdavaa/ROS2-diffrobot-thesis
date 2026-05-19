from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='aruco_opencv',
            executable='aruco_tracker_autostart',
            name='aruco_tracker',
            namespace='mapper_robot',
            output='screen',
            parameters=[
                {'cam_base_topic': '/mapper_robot/camera/image_raw'},
                {'marker_size': 0.15},
            ]
        ),
        Node(
            package='aruco_opencv',
            executable='aruco_tracker_autostart',
            name='aruco_tracker',
            namespace='localizer_robot',
            output='screen',
            parameters=[
                {'cam_base_topic': '/localizer_robot/camera/image_raw'},
                {'marker_size': 0.15},
            ]
        ),
    ])