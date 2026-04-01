import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, GroupAction, OpaqueFunction, RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, PushRosNamespace, SetRemap, SetParameter
from launch.conditions import IfCondition, UnlessCondition


def gopigo3_ros2_multi_launch_setup(context, *args, **kwargs):
    

    gopigo3_localizer_robot = GroupAction(
      actions=[
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('gopigo3_ros2'), 'launch'), '/gopigo3_ros2_launch.py']),
            launch_arguments={
                'robot_namespace': 'localizer_robot',
                'use_sim_time': 'True',
                'use_slam': 'False',
                'map_namespace': 'mapper_robot',
                'map': '',
                'spawn_only': 'True',
                #'spawn_shift_x': '0.0',
                #'spawn_shift_y': '0.0',
                #changed position so two robot won't collide
                'spawn_shift_x': '1.0',
                'spawn_shift_y': '0.5',
                'rviz_config': os.path.join(get_package_share_directory('gopigo3_ros2'), 'rviz', 'localizer_robot_sim.rviz')
            }.items(),
        ),
      ]
    )
    

    # Run the node
    return [
        gopigo3_localizer_robot,
    ]

def generate_launch_description():
  return LaunchDescription([
      OpaqueFunction(function=gopigo3_ros2_multi_launch_setup)
  ])