import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import GroupAction
from launch_ros.actions import Node, PushRosNamespace, SetRemap


def make_robot_aruco_localizer(robot_namespace: str):
    marker_file = os.path.join(
        get_package_share_directory('gopigo3_aruco'),
        'markers',
        'markers.yaml'
    )

    return GroupAction([
        PushRosNamespace(robot_namespace),

        # Keep each robot's TF isolated, matching the rest of the multi-robot system.
        SetRemap(src='/tf', dst=f'/{robot_namespace}/tf'),
        SetRemap(src='/tf_static', dst=f'/{robot_namespace}/tf_static'),

        Node(
            package='gopigo3_aruco',
            executable='aruco_localizer',
            name='aruco_localizer',
            output='screen',
            parameters=[
                {'use_sim_time': False},
                {'robot_namespace': robot_namespace},
                {'map_namespace': robot_namespace},
                {'aruco_marker_file_path': marker_file},
                {'aruco_world_frame': 'aruco_world'},
                {'aruco_camera_frame': f'{robot_namespace}/aruco_camera'},
                {'is_mapper': True},
                {'aruco_cooldown_time': 5.0},

                # Relative topic; inside namespace this becomes:
                # /robot_1/aruco_detections or /robot_2/aruco_detections
                {'aruco_detections': 'aruco_detections'},
            ],
        ),
    ])


def generate_launch_description():
    return LaunchDescription([
        make_robot_aruco_localizer('robot_1'),
        make_robot_aruco_localizer('robot_2'),
    ])