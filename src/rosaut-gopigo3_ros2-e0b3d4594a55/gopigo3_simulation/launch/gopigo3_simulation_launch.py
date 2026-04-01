import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction, DeclareLaunchArgument, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, PushRosNamespace, SetRemap
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
import xacro

 
def gopigo3_simulation_launch_setup(context, *args, **kwargs):

  robot_namespace = LaunchConfiguration('robot_namespace', default='')
  spawn_only = LaunchConfiguration('spawn_only', default='False')
  spawn_shift_x = LaunchConfiguration('spawn_shift_x', default='0.0')
  spawn_shift_y = LaunchConfiguration('spawn_shift_y', default='0.0')
  
  robot_namespace_arg = DeclareLaunchArgument('robot_namespace', default_value=robot_namespace)
  spawn_only_arg = DeclareLaunchArgument('spawn_only', default_value=spawn_only)
  spawn_shift_x_arg = DeclareLaunchArgument('spawn_shift_x', default_value=spawn_shift_x)
  spawn_shift_y_arg = DeclareLaunchArgument('spawn_shift_y', default_value=spawn_shift_y)

  print(spawn_only.perform(context))

  gopigo3_description_launch = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
      [os.path.join(get_package_share_directory('gopigo3_description'), 'launch'), '/gopigo3_description_launch.py']
    ),
    launch_arguments={
      'robot_namespace': robot_namespace,
      'use_sim_time': 'True'
    }.items()
  )

  #start gazebo simulation 
  gz = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
      [os.path.join(get_package_share_directory('gopigo3_simulation'), 'launch'), '/gz_include_launch.py']
    ),
    condition=UnlessCondition(spawn_only)
  )

  #start gazebo<->ROS bridge
  gz_bridge = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
      [os.path.join(get_package_share_directory('gopigo3_simulation'), 'launch'), '/gz_bridge_include_launch.py']
    )
  )

  #spawn_entities    
  spawn = GroupAction(
    actions=[
      PushRosNamespace(robot_namespace),
      Node(
        package='ros_gz_sim',
        executable='create',
        name= 'spawner',
        arguments=[
            '-name', '{}'.format(robot_namespace.perform(context)),
            '-topic', 'robot_description',
            '-x', '{}'.format(spawn_shift_x.perform(context)),
            '-y', '{}'.format(spawn_shift_y.perform(context)),
            '-z', '0.01'
        ],
        output='screen',
      )
    ]
  )

  return [
    robot_namespace_arg,
    spawn_only_arg,
    spawn_shift_x_arg,
    spawn_shift_y_arg,
    gopigo3_description_launch,
    gz,
    gz_bridge,
    spawn
  ]
  # opaque function end


def generate_launch_description():
  return LaunchDescription([
      OpaqueFunction(function=gopigo3_simulation_launch_setup)
  ])