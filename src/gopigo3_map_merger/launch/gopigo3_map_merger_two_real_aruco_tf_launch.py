from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='gopigo3_map_merger',
            executable='tf_relay',
            name='tf_relay_for_real_map_merger',
            output='screen',
            parameters=[
                {'use_sim_time': False},
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
                {'use_sim_time': False},
                {'map_topic_1': '/robot_1/map'},
                {'map_topic_2': '/robot_2/map'},
                {'output_topic': '/common/global_map'},

                # Real shared frame from physical/simulated ArUco markers.
                {'global_frame': 'aruco_world'},
                {'use_tf_alignment': True},

                {'map1_frame': 'robot_1/map'},
                {'map2_frame': 'robot_2/map'},

                # New stability parameters.
                {'merge_period_sec': 5.0},
                {'lock_tf_alignment': True},
                {'require_all_transforms': False},
            ],
        ),
    ])