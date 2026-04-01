import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, SetRemap
import xacro
 
 
def gopigo3_rviz_launch_setup(context, *args, **kwargs):
    
    robot_namespace = LaunchConfiguration('robot_namespace',default='')
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
 
    robot_namespace_arg = DeclareLaunchArgument('robot_namespace', default_value=robot_namespace)
    
    rviz2 = GroupAction(
      actions=[
        Node(
          package='rviz2',
          executable='rviz2',
          name='rviz2',
          arguments=['-d', os.path.join(get_package_share_directory('gopigo3_description'), 'rviz', 'gopigo3_single_model_real.rviz')],
          parameters=[
              {'use_sim_time': use_sim_time}        
          ]            
        )  
      ]
    )

    return [
        robot_namespace_arg,
        rviz2
    ]

def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=gopigo3_rviz_launch_setup)
    ])