# Milestones

## Milestone 1: ArUco-Based Multi-Robot Frame Alignment (Simulation)

In simulation, a multi-robot localization architecture was successfully validated using visual fiducial markers.

Both the mapper robot and the localizer robot were able to detect a shared ArUco marker using onboard camera sensors.

- The mapper robot computes and publishes a stable transform:
  aruco_world → mapper_robot/map

- The localizer robot uses marker detections to estimate its pose and publishes:
  /localizer_robot/initialpose

This pose is expressed in the mapper robot’s map frame.

### Key Results

- Established a shared global reference frame using ArUco markers
- Enabled cross-robot pose initialization
- Demonstrated multi-robot alignment without pre-shared maps

### Verified Topics

- /mapper_robot/aruco_detections
- /localizer_robot/aruco_detections
- /localizer_robot/initialpose

### Verified TF

- aruco_world → mapper_robot/map
