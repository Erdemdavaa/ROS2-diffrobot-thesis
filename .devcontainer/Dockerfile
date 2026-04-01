# FROM althack/ros2:humble-gazebo-2023-09-03 # last version with classic gazebo
FROM althack/ros2:humble-gazebo-2025-10-03

# ** Install additional packages. **

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
  && apt-get -y install --no-install-recommends mesa-utils mesa-va-drivers ros-humble-plotjuggler ros-humble-rqt* ros-humble-joint-state-publisher ros-humble-slam-toolbox ros-humble-nav2-bringup ros-humble-rmw-zenoh-cpp htop xterm ros-humble-aruco-opencv* \
  #
  # Clean up
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/*
ENV DEBIAN_FRONTEND=dialog

#ENV LIBVA_DRIVER_NAME=d3d12
#ENV LD_LIBRARY_PATH=/usr/lib/wsl/lib

# install ros-humble-rmw-cyclonedds-cpp
#ENV RMW_IMPLEMENTATION="rmw_cyclonedds_cpp"
#ENV HOST_ADDR="172.22.128.1"
#ENV CYCLONEDDS_URI="<CycloneDDS><Domain id='any'><General><AllowMulticast>false</AllowMulticast><ExternalNetworkAddress>${HOST_ADDR}</ExternalNetworkAddress></General><Compatibility><ManySocketsMode>none</ManySocketsMode></Compatibility><Discovery><ParticipantIndex>0</ParticipantIndex><Peers><Peer address='${HOST_ADDR}'/></Peers></Discovery><Tracing><Verbosity>config</Verbosity><Out>stderr</Out></Tracing></Domain></CycloneDDS>"

# Set up auto-source of workspace for ros user
ARG WORKSPACE
RUN echo "if [ -f ${WORKSPACE}/install/setup.bash ]; then source ${WORKSPACE}/install/setup.bash; fi" >> /home/ros/.bashrc