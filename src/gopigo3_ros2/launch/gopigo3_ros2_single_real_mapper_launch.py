import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def launch_setup(context, *args, **kwargs):
    robot_namespace = LaunchConfiguration('robot_namespace')
    map_namespace = LaunchConfiguration('map_namespace')
    use_slam = LaunchConfiguration('use_slam')
    teleop_key = LaunchConfiguration('teleop_key')
    rqt_tf_tree = LaunchConfiguration('rqt_tf_tree')
    rviz_config = LaunchConfiguration('rviz_config')

    gopigo3_ros2_share = get_package_share_directory('gopigo3_ros2')

    real_mapper = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gopigo3_ros2_share, 'launch', 'gopigo3_ros2_launch.py')
        ),
        launch_arguments={
            # Real robot namespace. This must match the robot-side topics:
            # /mapper_gopigo3/odom, /mapper_gopigo3/scan, /mapper_gopigo3/tf, ...
            'robot_namespace': robot_namespace,

            # Real robot uses wall-clock time, not Gazebo /clock.
            'use_sim_time': 'False',

            # Mapper robot runs SLAM.
            'use_slam': use_slam,

            # For the single-real-robot test, its own map namespace is used.
            'map_namespace': map_namespace,

            # No saved map needed in SLAM mode.
            'map': '',

            # Safer default: do not accidentally send velocity commands while testing.
            'teleop_key': teleop_key,

            # Useful for checking TF in lab.
            'rqt_tf_tree': rqt_tf_tree,

            # RViz config can still be changed manually after launch.
            'rviz_config': rviz_config,
        }.items(),
    )

    return [real_mapper]


def generate_launch_description():
    gopigo3_ros2_share = get_package_share_directory('gopigo3_ros2')
    default_rviz = os.path.join(gopigo3_ros2_share, 'rviz', 'mapper_robot_sim.rviz')

    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_namespace',
            default_value='mapper_gopigo3',
            description='Namespace used by the real mapper robot.'
        ),
        DeclareLaunchArgument(
            'map_namespace',
            default_value='mapper_gopigo3',
            description='Namespace of the map frame/topic used by this robot.'
        ),
        DeclareLaunchArgument(
            'use_slam',
            default_value='True',
            description='True means run SLAM Toolbox as mapper.'
        ),
        DeclareLaunchArgument(
            'teleop_key',
            default_value='False',
            description='Start keyboard teleop. Keep False during first lab checks.'
        ),
        DeclareLaunchArgument(
            'rqt_tf_tree',
            default_value='True',
            description='Open rqt_tf_tree for TF debugging.'
        ),
        DeclareLaunchArgument(
            'rviz_config',
            default_value=default_rviz,
            description='RViz config file.'
        ),
        OpaqueFunction(function=launch_setup),
    ])
