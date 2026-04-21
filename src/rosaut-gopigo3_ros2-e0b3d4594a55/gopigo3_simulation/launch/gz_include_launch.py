import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
  ros_gz_sim_dir = get_package_share_directory('ros_gz_sim')
  ros_gz_launch_dir = os.path.join(ros_gz_sim_dir, 'launch')

  world_pkg_name = 'gopigo3_simulation'
  world_file_subpath = 'worlds/gopigo3_example_world.sdf'
  world_file = os.path.join(get_package_share_directory(world_pkg_name), world_file_subpath)

  return LaunchDescription([
      IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(ros_gz_launch_dir, 'gz_sim.launch.py')),
        launch_arguments={
          'gz_args': world_file,
          'on_exit_shutdown': 'true'
        }.items(),
      )
  ])