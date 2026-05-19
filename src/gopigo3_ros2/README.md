# How to customize?

This project for *gopigo3* robot gives us a useful opportunity to regard and apply *gopigo3_ros2* package as a general template for basic function implementations from model representation to path planning for differential driven mobile robots.
Although solutions use mainly officially recommended default ROS2 packages, some particular changes are necessary to customize robot specific preferences either for simulation or real life applications.

## Mode configuration

In order to run basic all-purpose functionality for a robot, the following launch call is recommended:
```
ros2 launch gopigo3_ros2 gopigo3_ros2_launch.py
```
Running mode of the robot could be determined by predefined launch arguments:
  * **robot_namespace**: custom namespace and name of the robot (no "/" is needed, default value is '')
  * **use_sim_time**: Use True if you work in simulation and False otherwise (default value is True)
  * **use_slam**: If True, mapping is applied, if False, only localization (default value is True)
  * **map_namespace**: namespace of the mapper robot if only localization is applied (default value is the same as *robot_namespace*)
  * **spawn_only**: False if you want to launch simulation environment, True if simulator nodes are already launched by a launch call previously (default value is False)
  * **teleop_key**: Use True if you want to teleop_key controller terminal and False otherwise (default value is True)
  * **rviz_config**: Path of rviz config file to open for monitoring, rviz will not launch if '' is given (default value is '')
  * **rqt_tf_tree**: Use True if you want to get an rqt tf tree for the robot and False otherwise (default value is True)

## Robot model customization

In order to use this whole library with another robot, model description must be changed to current one. Therefore replace all the urdf and xacro files in *gopigo3_description* package *urdf* folder and all the mesh files in *meshes* folder with the new ones and update root description file in *gopigo3_description/launch/gopigo3_description_launch.py*.

## Simulation 

### Gazebo plugins

If another plugins are needed, they must be included in gazebo related xacro files as model description components.
Be aware that some necessary plugins must be added under *world* tag and some others under *robot* tag. Check official gazebo documentation for another information.

### Gazebo bridge

In this repository, Gazebo bridge system is prepared to be suitable for multirobot applications too. The concept is to separate global, simulation dependent topic bridging and individual robot dependent topic bridging to separate *gz_bridge* nodes. Therefore the number of bridge nodes during a simulation is the number of participating robots plus one.

If another topics are needed to be bridged, *common_gz_bridge* and *gz_bridge* node instances can be extended with necessary topics in *gopigo3_simulation/launch/gz_bridge_include_launch.py*.

### Simulation environment

For using another Gazebo world as a simulation environment, world file can be changed manually in *gopigo3_simulation/launch/gz_include_launch.py*. It is recommended to place new world files into the *worlds* folder.

Changing the spawn placement of a robot can also be modified manually by the spawn node implementation section in *gopigo3_simulation/launch/gopigo3_simulation_launch.py* file.

## Navigation customization

Navigation related functions are separated to three different units found in *gopigo3_navigation/launch/gopigo3_navigation_launch.py*. Depending on the running mode if whole slam functionality or only localization is needed, either only *slam_toolbox* and *nav2_bringup* or only *slam_toolbox* and *localization_bringup* are launched at a time.

### Configuration files

In order to handle namespaces and cross references for another namespaces, a custom parser script was implemented, and included templates are parsed in runtime according to namespace of the current robot and namespace of the mapper robot configured before.
Any parameters and placeholders for parser script can be changed or extended arbitrarily by overwrite necessary parts of some files found in *config* and *launch* directories of *gopigo3_navigation* package.