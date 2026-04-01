import os
import yaml
from launch.launch_description_sources import load_python_launch_file_as_module
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, PushRosNamespace, SetRemap, SetParameter
from launch.actions import GroupAction, DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace, SetRemap
from launch.conditions import IfCondition, UnlessCondition

def gopigo3_nav_sim_launch_setup(context, *args, **kwargs):

  robot_namespace = LaunchConfiguration('robot_namespace', default='')
  use_sim_time = LaunchConfiguration('use_sim_time', default='True')
  use_slam = LaunchConfiguration('use_slam', default='True')
  map_namespace = LaunchConfiguration('map_namespace', default=robot_namespace.perform(context))
  map_file = LaunchConfiguration('map', default='')
  spawn_shift_x = LaunchConfiguration('spawn_shift_x', default='0.0')
  spawn_shift_y = LaunchConfiguration('spawn_shift_y', default='0.0')

  robot_ns_sl = '' if robot_namespace.perform(context)=='' else robot_namespace.perform(context) + '/'
  robot_ns_ = '' if robot_namespace.perform(context)=='' else robot_namespace.perform(context) + '_'

  robot_namespace_arg = DeclareLaunchArgument('robot_namespace', default_value=robot_namespace)
  use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value=use_sim_time)
  use_slam_arg = DeclareLaunchArgument('use_slam', default_value=use_slam)
  map_namespace_arg = DeclareLaunchArgument('map_namespace', default_value=map_namespace)
  map_file_arg = DeclareLaunchArgument('map', default_value=map_file)
  spawn_shift_x_arg = DeclareLaunchArgument('spawn_shift_x', default_value=spawn_shift_x)
  spawn_shift_y_arg = DeclareLaunchArgument('spawn_shift_y', default_value=spawn_shift_y)

  template_slam_params_file = os.path.join(get_package_share_directory('gopigo3_navigation'),'config','template_slam_params.yaml')
  slam_params_file = os.path.join(get_package_share_directory('gopigo3_navigation'),'config','{}slam_params.yaml'.format(robot_ns_))
  yaml_parser_module = load_python_launch_file_as_module(os.path.join(get_package_share_directory('gopigo3_navigation'), 'launch', 'lib', 'gopigo3_navigation_param_module.py'))
  yaml_parser_module.gopigo3_navigation_parse_namespace_yaml_file(template_slam_params_file, slam_params_file, '[my_namespace]', robot_namespace.perform(context), '[map_namespace]', map_namespace.perform(context))
  
  slam_toolbox = GroupAction(
    actions=[
      PushRosNamespace(robot_namespace),
      SetRemap(src='/tf', dst='/{}tf'.format(robot_ns_sl)),
      SetRemap(src='/tf_static', dst='/{}tf_static'.format(robot_ns_sl)),
      IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
          get_package_share_directory('slam_toolbox'), 'launch'), '/online_async_launch.py']),
          launch_arguments={
            'use_sim_time' : use_sim_time,
            'slam_params_file': slam_params_file
          }.items(),
        condition=IfCondition(use_slam)
      ),
    ]
  )

  template_nav2_params_file = os.path.join(get_package_share_directory('gopigo3_navigation'),'config','template_nav2_params.yaml')
  nav2_params_file = os.path.join(get_package_share_directory('gopigo3_navigation'),'config','{}nav2_params.yaml'.format(robot_ns_))
  yaml_parser_module.gopigo3_navigation_parse_namespace_yaml_file(template_nav2_params_file, nav2_params_file, '[my_namespace]', robot_namespace.perform(context), '[map_namespace]', map_namespace.perform(context))

  nav2_bringup = GroupAction(
      actions=[
          PushRosNamespace(robot_namespace),
          # Identical remapping from /tf to /tf is necessary if you want to overwrite the remapping made by navigation_launch.py on a lower level
          SetRemap(src='/tf', dst='/{}tf'.format(robot_ns_sl)),
          SetRemap(src='/tf_static', dst='/{}tf_static'.format(robot_ns_sl)),
          IncludeLaunchDescription(
              PythonLaunchDescriptionSource([os.path.join(
                  get_package_share_directory('nav2_bringup'), 'launch'), '/navigation_launch.py']),
              launch_arguments={ 
                                'params_file': nav2_params_file,
                                'headless' : 'False',
                                'use_sim_time' : use_sim_time,
                                }.items(),
          )
      ]
  )

  localization_bringup = GroupAction(
      actions=[
          PushRosNamespace(robot_namespace),
          # Identical remapping from /tf to /tf is necessary if you want to overwrite the remapping made by localization_launch.py on a lower level
          SetRemap(src='/tf', dst='/{}tf'.format(robot_ns_sl)),
          SetRemap(src='/tf_static', dst='/{}tf_static'.format(robot_ns_sl)),
          IncludeLaunchDescription(
              PythonLaunchDescriptionSource([os.path.join(
                  get_package_share_directory('gopigo3_navigation'), 'launch'), '/_localization_launch.py']),
              launch_arguments={ 
                                'params_file': nav2_params_file,
                                'headless' : 'False',
                                'use_sim_time' : use_sim_time,
                                'map' : map_file,
                                'spawn_shift_x' : spawn_shift_x,
                                'spawn_shift_y' : spawn_shift_y,
                                }.items(),
              condition=UnlessCondition(use_slam)
          )
      ]
  )


  return [
    robot_namespace_arg,
    use_sim_time_arg,
    use_slam_arg,
    map_namespace_arg,
    map_file_arg,
    spawn_shift_x_arg,
    spawn_shift_y_arg,
    slam_toolbox,
    nav2_bringup,
    localization_bringup,
  ]

def generate_launch_description():
  return LaunchDescription([
      OpaqueFunction(function=gopigo3_nav_sim_launch_setup)
  ])