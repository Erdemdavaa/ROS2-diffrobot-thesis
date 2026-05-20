import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, PushRosNamespace, SetRemap
from launch.actions import GroupAction


def make_robot_aruco_group(robot_namespace: str):
    marker_file = os.path.join(
        get_package_share_directory('gopigo3_aruco'),
        'markers',
        'markers.yaml'
    )

    return GroupAction([
        PushRosNamespace(robot_namespace),

        # Keep TF isolated inside each robot namespace
        SetRemap(src='/tf', dst=f'/{robot_namespace}/tf'),
        SetRemap(src='/tf_static', dst=f'/{robot_namespace}/tf_static'),

        # ArUco detector from camera image
        Node(
            package='aruco_opencv',
            executable='aruco_tracker_autostart',
            name='aruco_tracker',
            output='screen',
            parameters=[
                {'use_sim_time': True},
                {'cam_base_topic': 'camera/image_raw'},
                {'marker_size': 0.15},
            ],
        ),

        # Our localizer node that converts detections into map/world relation
        Node(
            package='gopigo3_aruco',
            executable='aruco_localizer',
            name='aruco_localizer',
            output='screen',
            parameters=[
                {'use_sim_time': True},
                {'robot_namespace': robot_namespace},
                {'map_namespace': robot_namespace},
                {'aruco_marker_file_path': marker_file},
                {'aruco_world_frame': 'aruco_world'},
                {'aruco_camera_frame': f'{robot_namespace}/aruco_camera'},
                {'is_mapper': True},
                {'aruco_cooldown_time': 5.0},
                {'aruco_detections': 'aruco_detections'},
            ],
        ),
    ])


def generate_launch_description():
    return LaunchDescription([
        make_robot_aruco_group('robot_1'),
        make_robot_aruco_group('robot_2'),
    ])