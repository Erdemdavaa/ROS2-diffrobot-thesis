import os

from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import load_python_launch_file_as_module

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, OpaqueFunction, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, PushRosNamespace
from launch.substitutions import LaunchConfiguration
from launch.conditions import UnlessCondition

def gz_bridge_include_launch_setup(context, *args, **kwargs):

  robot_namespace = LaunchConfiguration('robot_namespace', default='')
  spawn_only = LaunchConfiguration('spawn_only', default='False')
  
  robot_ns_sl = '' if robot_namespace.perform(context)=='' else robot_namespace.perform(context) + '/'
  robot_ns_ = '' if robot_namespace.perform(context)=='' else robot_namespace.perform(context) + '_'

  # Gz - ROS Bridge for common topics like /clock
  # Somehow, using a yaml configuration file for /clock bridging is crashing like bridging direction would not be properly set.
  common_gz_bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    name= 'common_gz_bridge',
    arguments=[
      # Clock (IGN -> ROS2)
      '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
    ],
    output='screen',
    condition=UnlessCondition(spawn_only)
  )

  # Gz - ROS Bridge
  yaml_parser_module = load_python_launch_file_as_module(os.path.join(get_package_share_directory('gopigo3_simulation'), 'launch', 'lib', 'gopigo3_simulation_param_module.py'))
  
  template_gz_bridge_config_file = os.path.join(get_package_share_directory('gopigo3_simulation'),'config','template_gz_bridge_config.yaml')
  gz_bridge_config_file = os.path.join(get_package_share_directory('gopigo3_simulation'),'config','{}gz_bridge_config.yaml'.format(robot_ns_))
  yaml_parser_module.gopigo3_simulation_parse_namespace_yaml_file(template_gz_bridge_config_file, gz_bridge_config_file, '[my_namespace]', robot_namespace.perform(context))
  
  gz_bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    name= '{}gz_bridge'.format(robot_ns_),
    parameters=[
      {'config_file': gz_bridge_config_file,
       'expand_gz_topic_names': False
      }
    ],
    output='screen',
  )


  return [
    common_gz_bridge,
    gz_bridge
  ]

def generate_launch_description():
  return LaunchDescription([
      OpaqueFunction(function=gz_bridge_include_launch_setup)
  ])