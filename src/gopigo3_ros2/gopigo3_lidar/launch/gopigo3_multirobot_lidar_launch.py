import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace


def generate_launch_description():
    
    #lidar node
    # PushRosNamespace('robot1')
    gopigo3_lidar1 = Node(
        package='gopigo3_lidar',
        executable='scan_processor',
        parameters=[{'scan_raw_topic_name': '/robot1/scan'}],
        namespace='/robot1'
    )
    # PushRosNamespace('robot2')
    gopigo3_lidar2 = Node(
        package='gopigo3_lidar',
        executable='scan_processor',
        parameters=[{'scan_raw_topic_name': '/robot2/scan'}],
        namespace='/robot2'
    )

    # Run the node
    return LaunchDescription([
        gopigo3_lidar1
        # gopigo3_lidar2
    ])