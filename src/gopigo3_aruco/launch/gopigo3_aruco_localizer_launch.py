import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction, DeclareLaunchArgument, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, PushRosNamespace, SetRemap
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
import xacro

 
def gopigo3_aruco_localizer_launch_setup(context, *args, **kwargs):

  robot_namespace = LaunchConfiguration('robot_namespace', default='')
  aruco_marker_file_path = LaunchConfiguration('aruco_marker_file_path', default='')
  aruco_world_frame = LaunchConfiguration('aruco_world_frame', default='aruco_world')
  map_namespace = LaunchConfiguration('map_namespace', default=robot_namespace)
  aruco_camera_frame = LaunchConfiguration('aruco_camera_frame', default='camera')
  is_mapper = LaunchConfiguration('is_mapper', default='true')
  aruco_cooldown_time = LaunchConfiguration('aruco_cooldown_time', default='5.0')
  
  robot_namespace_arg = DeclareLaunchArgument('robot_namespace', default_value=robot_namespace)
  aruco_marker_file_path_arg = DeclareLaunchArgument('aruco_marker_file_path', default_value=aruco_marker_file_path)
  aruco_world_frame_arg = DeclareLaunchArgument('aruco_world_frame', default_value=aruco_world_frame)
  map_namespace_arg = DeclareLaunchArgument('map_namespace', default_value=map_namespace)
  aruco_camera_frame_arg = DeclareLaunchArgument('aruco_camera_frame', default_value=aruco_camera_frame)
  is_mapper_arg = DeclareLaunchArgument('is_mapper', default_value=is_mapper)
  aruco_cooldown_time_arg = DeclareLaunchArgument('aruco_cooldown_time', default_value=aruco_cooldown_time)

  robot_ns_sl = '' if robot_namespace.perform(context)=='' else robot_namespace.perform(context) + '/'

  gopigo3_aruco_localizer = GroupAction(
    actions=[
      PushRosNamespace(robot_namespace),
      SetRemap(src='/tf', dst='/{}tf'.format(robot_ns_sl)),
      SetRemap(src='/tf_static', dst='/{}tf_static'.format(robot_ns_sl)),
      Node(
        package='gopigo3_aruco',
        executable='aruco_localizer',
        name='aruco_localizer',
        output='screen',
        parameters=[{'robot_namespace': robot_namespace,
                    'aruco_marker_file_path': aruco_marker_file_path,
                    'aruco_world_frame': aruco_world_frame,
                    'map_namespace': map_namespace,
                    'aruco_camera_frame': aruco_camera_frame,
                    'is_mapper': is_mapper,
                    'aruco_cooldown_time': aruco_cooldown_time,}
        ], # add other parameters here if required
      )
    ]
  )

  return [
    robot_namespace_arg,
    aruco_marker_file_path_arg,
    aruco_world_frame_arg,
    map_namespace_arg,
    aruco_camera_frame_arg,
    is_mapper_arg,
    aruco_cooldown_time_arg,
    gopigo3_aruco_localizer
  ]
  # opaque function end


def generate_launch_description():
  return LaunchDescription([
      OpaqueFunction(function=gopigo3_aruco_localizer_launch_setup)
  ])