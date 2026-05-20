from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='gopigo3_map_merger',
            executable='tf_relay',
            name='tf_relay_for_map_merger',
            output='screen',
            parameters=[
                {'use_sim_time': True},
                {'tf_topics': ['/robot_1/tf', '/robot_2/tf']},
                {'tf_static_topics': ['/robot_1/tf_static', '/robot_2/tf_static']},
            ],
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

                # Use the ArUco world frame as the shared map-merging frame.
                {'global_frame': 'aruco_world'},
                {'use_tf_alignment': True},

                {'map1_frame': 'robot_1/map'},
                {'map2_frame': 'robot_2/map'},
            ],
        ),
    ])
