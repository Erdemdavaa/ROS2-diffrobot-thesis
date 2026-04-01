import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, OpaqueFunction, GroupAction
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, PushRosNamespace


def gopigo3_teleop_launch_setup(context, *args, **kwargs):

  robot_namespace = LaunchConfiguration('robot_namespace', default='')
  robot_namespace_arg = DeclareLaunchArgument('robot_namespace', default_value=robot_namespace)
  
  # Configure the node
  teleop = GroupAction(
    actions=[
      PushRosNamespace(robot_namespace),
      Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        output='screen',
        prefix = 'xterm -e',
        name= 'teleop_key',
      )
    ]
  )

  # Run the node
  return [
    robot_namespace_arg,
    teleop,
  ]

def generate_launch_description():
  return LaunchDescription([
      OpaqueFunction(function=gopigo3_teleop_launch_setup)
  ])