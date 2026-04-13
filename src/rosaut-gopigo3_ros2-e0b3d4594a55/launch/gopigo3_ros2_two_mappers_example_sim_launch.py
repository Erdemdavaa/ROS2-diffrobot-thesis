import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import GroupAction, OpaqueFunction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def gopigo3_ros2_two_mappers_launch_setup(context, *args, **kwargs):

    common_simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory('gopigo3_simulation'),
                    'launch'
                ),
                '/gopigo3_simulation_common_launch.py'
            ]
        )
    )

    gopigo3_robot_1 = GroupAction(
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [
                        os.path.join(
                            get_package_share_directory('gopigo3_ros2'),
                            'launch'
                        ),
                        '/gopigo3_ros2_launch.py'
                    ]
                ),
                launch_arguments={
                    'robot_namespace': 'robot_1',
                    'use_sim_time': 'True',
                    'use_slam': 'True',
                    'map_namespace': 'robot_1',
                    'map': '',
                    'spawn_shift_x': '0.0',
                    'spawn_shift_y': '0.0',
                    'rviz_config': '',
                    'rqt_tf_tree': 'False',
                }.items(),
            ),
        ]
    )

    gopigo3_robot_2 = GroupAction(
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [
                        os.path.join(
                            get_package_share_directory('gopigo3_ros2'),
                            'launch'
                        ),
                        '/gopigo3_ros2_launch.py'
                    ]
                ),
                launch_arguments={
                    'robot_namespace': 'robot_2',
                    'use_sim_time': 'True',
                    'use_slam': 'True',
                    'map_namespace': 'robot_2',
                    'map': '',
                    'spawn_shift_x': '1.0',
                    'spawn_shift_y': '0.5',
                    'rviz_config': '',
                    'rqt_tf_tree': 'False',
                }.items(),
            ),
        ]
    )

    return [
        common_simulation,
        gopigo3_robot_1,
        gopigo3_robot_2,
    ]


def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=gopigo3_ros2_two_mappers_launch_setup)
    ])