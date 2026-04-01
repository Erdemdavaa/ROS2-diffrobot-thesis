import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, SetRemap, PushRosNamespace
import xacro
 
 
def gopigo3_description_launch_setup(context, *args, **kwargs):

    robot_namespace = LaunchConfiguration('robot_namespace',default='cica')
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    robot_ns_sl = '' if robot_namespace.perform(context)=='' else robot_namespace.perform(context) + '/'

    gopigo3_description_pkg_name = 'gopigo3_description'
    robot_description_file_subpath = 'urdf/gopigo3.xacro'
    # Use xacro to process the file
    xacro_file = os.path.join(get_package_share_directory(gopigo3_description_pkg_name),robot_description_file_subpath)
    # Do not write e.g. '/robot1' for ns mapping because "/" is forbidden by some gazebo plugin configs
    robot_description_raw = xacro.process_file(xacro_file, mappings={
        'ns' : '{}'.format(robot_ns_sl)
        }).toxml()

    robot_namespace_arg = DeclareLaunchArgument('robot_namespace', default_value=robot_namespace)
    
    robot_state_publisher = GroupAction(
      actions=[
        PushRosNamespace(robot_namespace),
        SetRemap(src='/tf', dst='/{}tf'.format(robot_ns_sl)),
        SetRemap(src='/tf_static', dst='/{}tf_static'.format(robot_ns_sl)),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name= 'robot_state_publisher',
            output='screen',     
            parameters=[{'robot_description': robot_description_raw,
                        'use_sim_time': use_sim_time,                    
                        }
            ],
        )
      ]
    )
 
    joint_state_publisher = GroupAction(
      actions=[
        PushRosNamespace(robot_namespace),
        SetRemap(src='/tf', dst='/{}tf'.format(robot_ns_sl)),
        SetRemap(src='/tf_static', dst='/{}tf_static'.format(robot_ns_sl)),
        Node(
          package='joint_state_publisher',
          executable='joint_state_publisher',
          name= 'joint_state_publisher',
          output='screen',
          parameters=[{'robot_description': robot_description_raw,
                      'use_sim_time': use_sim_time}
          ], # add other parameters here if required
        )
      ]
    )

    return [
        robot_namespace_arg,
        robot_state_publisher,
        joint_state_publisher
    ]

def generate_launch_description():
  return LaunchDescription([
      OpaqueFunction(function=gopigo3_description_launch_setup)
  ])
