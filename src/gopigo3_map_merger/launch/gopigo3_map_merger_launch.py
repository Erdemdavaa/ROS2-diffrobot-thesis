from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='common_map_tf_pub',
            arguments=['0', '0', '0', '0', '0', '0', 'world', 'common_map'],
            parameters=[{'use_sim_time': True}],
            output='screen',
        ),
        Node(
            package='gopigo3_map_merger',
            executable='map_merger',
            name='map_merger',
            output='screen',
            parameters=[
                {'use_sim_time': True},
                {'map_topic_1': '/robot_1/map'},
                {'map_topic_2': '/robot_2/map'},
                {'output_topic': '/common/global_map'},
            ]
        ),
        Node(
            package='gopigo3_map_merger',
            executable='tf_relay',
            name='tf_relay',
            output='screen',
            parameters=[
                {'use_sim_time': True},
                {'tf_topics': ['/robot_1/tf', '/robot_2/tf']},
                {'tf_static_topics': ['/robot_1/tf_static', '/robot_2/tf_static']},
            ]
        )
    ])