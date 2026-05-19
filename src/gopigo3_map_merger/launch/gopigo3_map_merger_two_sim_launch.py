from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('map_topic_1', default_value='/robot_1/map'),
        DeclareLaunchArgument('map_topic_2', default_value='/robot_2/map'),
        DeclareLaunchArgument('output_topic', default_value='/common/global_map'),
        DeclareLaunchArgument('global_frame', default_value='common_map'),

        DeclareLaunchArgument('map1_offset_x', default_value='0.0'),
        DeclareLaunchArgument('map1_offset_y', default_value='0.0'),
        DeclareLaunchArgument('map1_yaw', default_value='0.0'),

        DeclareLaunchArgument('map2_offset_x', default_value='1.0'),
        DeclareLaunchArgument('map2_offset_y', default_value='0.5'),
        DeclareLaunchArgument('map2_yaw', default_value='0.0'),

        Node(
            package='gopigo3_map_merger',
            executable='map_merger',
            name='map_merger',
            output='screen',
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'map_topic_1': LaunchConfiguration('map_topic_1'),
                'map_topic_2': LaunchConfiguration('map_topic_2'),
                'output_topic': LaunchConfiguration('output_topic'),
                'global_frame': LaunchConfiguration('global_frame'),

                'map1_offset_x': LaunchConfiguration('map1_offset_x'),
                'map1_offset_y': LaunchConfiguration('map1_offset_y'),
                'map1_yaw': LaunchConfiguration('map1_yaw'),

                'map2_offset_x': LaunchConfiguration('map2_offset_x'),
                'map2_offset_y': LaunchConfiguration('map2_offset_y'),
                'map2_yaw': LaunchConfiguration('map2_yaw'),
            }],
        ),
    ])