import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, GroupAction, OpaqueFunction, RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, PushRosNamespace, SetRemap, SetParameter
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import PythonExpression


def gopigo3_ros2_launch_setup(context, *args, **kwargs):

    robot_namespace = LaunchConfiguration('robot_namespace', default='')
    use_sim_time = LaunchConfiguration('use_sim_time', default='True')
    use_slam = LaunchConfiguration('use_slam', default='True')
    map_namespace = LaunchConfiguration('map_namespace', default=robot_namespace.perform(context))
    map_file = LaunchConfiguration('map', default='')
    spawn_only = LaunchConfiguration('spawn_only', default='False')
    spawn_shift_x = LaunchConfiguration('spawn_shift_x', default='0.0')
    spawn_shift_y = LaunchConfiguration('spawn_shift_y', default='0.0')
    teleop_key = LaunchConfiguration('teleop_key', default='True')
    rviz_config = LaunchConfiguration('rviz_config', default='')
    rqt_tf_tree = LaunchConfiguration('rqt_tf_tree', default='True')

    robot_ns_sl = '' if robot_namespace.perform(context)=='' else robot_namespace.perform(context) + '/'

    robot_namespace_arg = DeclareLaunchArgument('robot_namespace', default_value=robot_namespace)
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value=use_sim_time)
    use_slam_arg = DeclareLaunchArgument('use_slam', default_value=use_slam)
    map_namespace_arg = DeclareLaunchArgument('map_namespace', default_value=map_namespace)
    map_file_arg = DeclareLaunchArgument('map', default_value=map_file)
    spawn_only_arg = DeclareLaunchArgument('spawn_only', default_value=spawn_only)
    spawn_shift_x_arg = DeclareLaunchArgument('spawn_shift_x', default_value=spawn_shift_x)
    spawn_shift_y_arg = DeclareLaunchArgument('spawn_shift_y', default_value=spawn_shift_y)
    teleop_key_arg = DeclareLaunchArgument('teleop_key', default_value=teleop_key)
    rviz_config_arg = DeclareLaunchArgument('rviz_config', default_value=rviz_config)
    rqt_tf_tree_arg = DeclareLaunchArgument('rqt_tf_tree', default_value=rqt_tf_tree)
        
    
    gopigo3_description = GroupAction(
      actions=[
        IncludeLaunchDescription(
          PythonLaunchDescriptionSource([os.path.join(
              get_package_share_directory('gopigo3_description'), 'launch'), '/gopigo3_description_launch.py']),
          launch_arguments={
              'robot_namespace': robot_namespace,
              'use_sim_time': use_sim_time,
          }.items(),
          condition = UnlessCondition(use_sim_time)
        ),
        SetRemap(src='/tf', dst='/{}tf'.format(robot_ns_sl)),
        SetRemap(src='/tf_static', dst='/{}tf_static'.format(robot_ns_sl)),
      ]
    )
    
    gopigo3_simulation = GroupAction(
      actions=[
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('gopigo3_simulation'), 'launch'), '/gopigo3_simulation_launch.py']),
            launch_arguments={
                'robot_namespace': robot_namespace
            }.items(),
            condition = IfCondition(use_sim_time)
        ),
        SetRemap(src='/tf', dst='/{}tf'.format(robot_ns_sl)),
        SetRemap(src='/tf_static', dst='/{}tf_static'.format(robot_ns_sl)),
      ]
    )
    
    gopigo3_teleop = GroupAction(
      actions=[
        IncludeLaunchDescription(
          PythonLaunchDescriptionSource([os.path.join(
              get_package_share_directory('gopigo3_teleop'), 'launch'), '/gopigo3_teleop_launch.py']),
          launch_arguments={
              'robot_namespace': robot_namespace
          }.items(),
          condition= IfCondition(teleop_key)
        ),
        SetRemap(src='/tf', dst='/{}tf'.format(robot_ns_sl)),
        SetRemap(src='/tf_static', dst='/{}tf_static'.format(robot_ns_sl)),
      ]
    )
    
    gopigo3_navigation = GroupAction(
      actions=[
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('gopigo3_navigation'), 'launch'), '/gopigo3_navigation_launch.py']),
            launch_arguments={
                'robot_namespace': robot_namespace,
                'use_sim_time': use_sim_time,
                'use_slam': use_slam,
                'map_namespace': map_namespace,
                'map': map_file,
            }.items()
        ),
        SetRemap(src='/tf', dst='/{}tf'.format(robot_ns_sl)),
        SetRemap(src='/tf_static', dst='/{}tf_static'.format(robot_ns_sl)),
      ]
    )

    gopigo3_rviz = GroupAction(
        actions=[
            PushRosNamespace(robot_namespace),
            Node(
                package='rviz2',
                executable='rviz2',
                name='rviz2',
                output='screen',
                parameters=[{'use_sim_time': use_sim_time}],
                arguments=['-d', rviz_config.perform(context)],
                remappings=[
                  ('/goal_pose', '/{}goal_pose'.format(robot_ns_sl)),
                  ('/tf', '/{}tf'.format(robot_ns_sl)),
                  ('/tf_static', '/{}tf_static'.format(robot_ns_sl)),
                ],
                condition= IfCondition(PythonExpression(["'", rviz_config, "' != ''"]))
            )
        ]
    )

    gopigo3_tf_tree = GroupAction(
      actions=[
        PushRosNamespace(robot_namespace),
        Node(
            package='rqt_tf_tree',
            executable='rqt_tf_tree',
            name='rqt_tf_tree',
            output='screen',
            remappings=[
              ('/tf', '/{}tf'.format(robot_ns_sl)),
              ('/tf_static', '/{}tf_static'.format(robot_ns_sl)),
            ],
            condition= IfCondition(rqt_tf_tree)
        )
      ]
    )

    gopigo3_environment_start = GroupAction(
        actions=[
            gopigo3_description,
            gopigo3_simulation,
            gopigo3_teleop,
            gopigo3_navigation
        ]
    )

    # Run the node
    return [
        robot_namespace_arg,
        use_sim_time_arg,
        use_slam_arg,
        map_namespace_arg,
        map_file_arg,
        spawn_only_arg,
        spawn_shift_x_arg,
        spawn_shift_y_arg,
        teleop_key_arg,
        rviz_config_arg,
        rqt_tf_tree_arg,
        gopigo3_rviz,
        gopigo3_tf_tree,
        gopigo3_environment_start,
    ]

def generate_launch_description():
  return LaunchDescription([
      OpaqueFunction(function=gopigo3_ros2_launch_setup)
  ])