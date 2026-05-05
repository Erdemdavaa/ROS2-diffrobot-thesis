Simulation mode:
  unset RMW_IMPLEMENTATION
  ros2 daemon stop
  ros2 daemon start
  source /opt/ros/humble/setup.bash
  source install/setup.bash

Real robot mode:
  export RMW_IMPLEMENTATION=rmw_zenoh_cpp
  ros2 run rmw_zenoh_cpp rmw_zenohd
  source /opt/ros/humble/setup.bash
  source install/setup.bash