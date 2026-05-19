import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def launch_setup(context, *args, **kwargs):
    robot_namespace = LaunchConfiguration('robot_namespace')
    map_namespace = LaunchConfiguration('map_namespace')
    teleop_key = LaunchConfiguration('teleop_key')
    rqt_tf_tree = LaunchConfiguration('rqt_tf_tree')
    rviz_config = LaunchConfiguration('rviz_config')

    aruco_world_frame = LaunchConfiguration('aruco_world_frame')
    aruco_camera_frame = LaunchConfiguration('aruco_camera_frame')
    aruco_detections = LaunchConfiguration('aruco_detections')
    aruco_marker_file_path = LaunchConfiguration('aruco_marker_file_path')
    aruco_cooldown_time = LaunchConfiguration('aruco_cooldown_time')

    gopigo3_ros2_share = get_package_share_directory('gopigo3_ros2')
    gopigo3_aruco_share = get_package_share_directory('gopigo3_aruco')

    # First start the normal real mapper stack.
    real_mapper = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gopigo3_ros2_share, 'launch', 'gopigo3_ros2_launch.py')
        ),
        launch_arguments={
            'robot_namespace': robot_namespace,
            'use_sim_time': 'False',
            'use_slam': 'True',
            'map_namespace': map_namespace,
            'map': '',
            'teleop_key': teleop_key,
            'rqt_tf_tree': rqt_tf_tree,
            'rviz_config': rviz_config,
        }.items(),
    )

    # Then start only the ArUco localizer.
    # The real robot already runs camera / tracker nodes, so this launch does NOT start a detector.
    aruco_localizer = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gopigo3_aruco_share, 'launch', 'gopigo3_aruco_localizer_launch.py')
        ),
        launch_arguments={
            'robot_namespace': robot_namespace,
            'is_mapper': 'true',
            'map_namespace': map_namespace,
            'aruco_world_frame': aruco_world_frame,
            'aruco_camera_frame': aruco_camera_frame,
            'aruco_detections': aruco_detections,
            'aruco_marker_file_path': aruco_marker_file_path,
            'aruco_cooldown_time': aruco_cooldown_time,
        }.items(),
    )

    return [
        real_mapper,
        aruco_localizer,
    ]


def generate_launch_description():
    gopigo3_ros2_share = get_package_share_directory('gopigo3_ros2')
    gopigo3_aruco_share = get_package_share_directory('gopigo3_aruco')

    default_rviz = os.path.join(gopigo3_ros2_share, 'rviz', 'mapper_robot_sim.rviz')
    default_marker_file = os.path.join(gopigo3_aruco_share, 'markers', 'markers.yaml')

    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_namespace',
            default_value='mapper_gopigo3',
            description='Namespace used by the real mapper robot.'
        ),
        DeclareLaunchArgument(
            'map_namespace',
            default_value='mapper_gopigo3',
            description='Namespace of the mapper robot map frame/topic.'
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
        DeclareLaunchArgument(
            'aruco_world_frame',
            default_value='aruco_world',
            description='Global ArUco reference frame.'
        ),
        DeclareLaunchArgument(
            'aruco_camera_frame',
            default_value='mapper_gopigo3/aruco_camera',
            description='Camera frame used by real robot ArUco detections.'
        ),
        DeclareLaunchArgument(
            'aruco_detections',
            default_value='/mapper_gopigo3/aruco_detections',
            description='Real robot ArUco detection topic.'
        ),
        DeclareLaunchArgument(
            'aruco_marker_file_path',
            default_value=default_marker_file,
            description='YAML file containing known marker poses.'
        ),
        DeclareLaunchArgument(
            'aruco_cooldown_time',
            default_value='5.0',
            description='Cooldown time between ArUco localization updates.'
        ),
        OpaqueFunction(function=launch_setup),
    ])
