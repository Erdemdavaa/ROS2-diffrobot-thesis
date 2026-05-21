# Thesis Demo Protocol: Multi-Robot SLAM Map Merging

This document records the current working thesis demonstration for two GoPiGo3 robots in simulation.

The current goal is to run two robots, let both robots build their own SLAM maps, use ArUco markers to estimate each robot map frame in a common reference frame, and publish one merged global occupancy grid.

## Current Working Concept

The current system has three main parts:

1. Two simulated robots run SLAM independently.
2. ArUco marker detection estimates the transform from `aruco_world` to each robot map frame.
3. The map merger transforms both robot maps into the common `aruco_world` frame and publishes `/common/global_map`.

The important result is:

```text
/robot_1/map  +  TF aruco_world -> robot_1/map
/robot_2/map  +  TF aruco_world -> robot_2/map
        ↓
/common/global_map
frame_id: aruco_world