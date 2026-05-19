import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    
    #lidar node
    gopigo3_lidar = Node(
        package='gopigo3_lidar',
        executable='scan_processor',
        parameters=[{'scan_raw_topic_name': '/scan'}]
    )

    # Run the node
    return LaunchDescription([
        gopigo3_lidar
    ])