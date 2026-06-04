import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def make_real_mapper(robot_namespace: str):
    gopigo3_ros2_share = get_package_share_directory('gopigo3_ros2')

    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gopigo3_ros2_share, 'launch', 'gopigo3_ros2_launch.py')
        ),
        launch_arguments={
            'robot_namespace': robot_namespace,
            'use_sim_time': 'False',
            'use_slam': 'True',
            'map_namespace': robot_namespace,
            'map': '',

            # Real robot is already physically present, so no Gazebo spawn.
            # Keep keyboard teleop and debug GUI off by default for safer lab startup.
            'teleop_key': 'False',
            'rqt_tf_tree': 'False',
            'rviz_config': '',
        }.items(),
    )


def generate_launch_description():
    return LaunchDescription([
        make_real_mapper('robot_1'),
        make_real_mapper('robot_2'),
    ])