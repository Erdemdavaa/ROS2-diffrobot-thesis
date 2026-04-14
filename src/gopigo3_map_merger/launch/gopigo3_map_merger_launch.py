from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='common_map_tf_pub',
            arguments=['0', '0', '0', '0', '0', '0', 'world', 'common_map'],
            output='screen',
        ),
        Node(
            package='gopigo3_map_merger',
            executable='map_merger',
            name='map_merger',
            output='screen',
            parameters=[
                {'map_topic_1': '/robot_1/map'},
                {'map_topic_2': '/robot_2/map'},
                {'output_topic': '/common/global_map'},
            ]
        )
    ])