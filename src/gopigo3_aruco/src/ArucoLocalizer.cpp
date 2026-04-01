#include <../include/ArucoLocalizer.h>
#include <yaml-cpp/yaml.h>
#include <tf2/LinearMath/Matrix3x3.h>
#include <tf2/LinearMath/Scalar.h>
#include <tf2/LinearMath/Quaternion.hpp>
#include <tf2/LinearMath/Transform.hpp>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>

using std::placeholders::_1;
using namespace std;

ArucoLocalizer::ArucoLocalizer() : Node("aruco_localizer")
{
  this->declare_parameter("robot_namespace", "");
  string param_robot_namespace = this->get_parameter("robot_namespace").as_string();
  string robot_ns_sl = (param_robot_namespace == "") ? "" : param_robot_namespace + "/";
  this->declare_parameter("aruco_marker_file_path", "");
  this->declare_parameter("aruco_world_frame", "aruco_world");
  this->declare_parameter("map_namespace", param_robot_namespace);
  string param_map_namespace = this->get_parameter("map_namespace").as_string();
  string map_ns_sl = (param_map_namespace == "") ? "" : param_map_namespace + "/";
  this->declare_parameter("aruco_camera_frame", robot_ns_sl + "aruco_camera");
  this->declare_parameter("base_frame", robot_ns_sl + "base_footprint");
  this->declare_parameter("is_mapper", true);
  this->declare_parameter("aruco_cooldown_time", 5.0);
  this->declare_parameter("aruco_detections", "aruco_detections");

  this->tf_buffer = std::make_unique<tf2_ros::Buffer>(this->get_clock());
  this->tf_buffer->setUsingDedicatedThread(true);
  this->tf_listener = std::make_shared<tf2_ros::TransformListener>(*(this->tf_buffer));
  this->tf_broadcaster = std::make_unique<tf2_ros::TransformBroadcaster>(*this);
  this->T_correction_marker_in_camera =
      tf2::Transform(tf2::Matrix3x3(0, 0, 1, -1, 0, 0, 0, -1, 0), tf2::Vector3(0, 0, 0));

  // Create a transform listener listening to mapper robot's tf topics
  this->tf_buffer_aruco = std::make_unique<tf2_ros::Buffer>(this->get_clock());
  this->tf_buffer_aruco->setUsingDedicatedThread(true);
  this->inner_node_tf_listener_aruco = std::make_shared<rclcpp::Node>(
      "tf_listener_aruco_internal", this->get_namespace(),
      rclcpp::NodeOptions().arguments(
          { "--ros-args", "-r", "/tf:=/" + map_ns_sl + "tf", "-r", "/tf_static:=/" + map_ns_sl + "tf_static" }));
  this->tf_listener_aruco =
      std::make_shared<tf2_ros::TransformListener>(*(this->tf_buffer_aruco), inner_node_tf_listener_aruco, false);

  this->initialpose_pub = this->create_publisher<geometry_msgs::msg::PoseWithCovarianceStamped>("initialpose", 10);

  auto qos = rclcpp::SensorDataQoS();
  qos.keep_last(1);
  this->aruco_sub = this->create_subscription<aruco_opencv_msgs::msg::ArucoDetection>(
      this->get_parameter("aruco_detections").as_string(), qos,
      std::bind(&ArucoLocalizer::aruco_detection_callback, this, _1));

  this->last_initialpose_publish_time = this->get_clock()->now();
  this->last_processing_time = this->get_clock()->now();
}

void ArucoLocalizer::aruco_detection_callback(const aruco_opencv_msgs::msg::ArucoDetection msg)
{
  // Return if no enough time was elapsed since last processing or initialpose publish
  if ((this->get_clock()->now() - this->last_processing_time).nanoseconds() < (0.5 * 1e9))
    return;
  this->last_processing_time = this->get_clock()->now();
  if (!this->get_parameter("is_mapper").as_bool() &&
      ((this->get_clock()->now() - this->last_initialpose_publish_time).nanoseconds() <
       (this->get_parameter("aruco_cooldown_time").as_double() * 1e9)))
  {
    return;
  }

  if (msg.markers.empty())
  {
    RCLCPP_INFO(this->get_logger(), "No markers detected.");
    return;
  }

  auto aruco_marker_file_path = this->get_parameter("aruco_marker_file_path").as_string();
  if (aruco_marker_file_path.empty())
  {
    RCLCPP_ERROR(this->get_logger(), "No marker file path specified.");
    return;
  }
  YAML::Node marker_file = YAML::LoadFile(aruco_marker_file_path);
  auto marker_map = marker_file["markers"];

  // ++++++ Section of collecting camera pose candidates in world frame into a vector ++++++ //
  std::vector<tf2::Transform> poses_camera_in_world;
  poses_camera_in_world.clear();
  for (const auto& m : msg.markers)
  {
    auto key = std::to_string(m.marker_id);
    if (!marker_map[key])
    {
      RCLCPP_WARN(this->get_logger(), "Marker ID %d not found in YAML marker map file, skipping.", m.marker_id);
      continue;
    }
    // Pose of marker in world frame according to YAML
    auto marker_in_world = marker_map[key];
    auto T_marker_in_world = tf2::Transform(tf2::Quaternion(marker_in_world["orientation"].as<std::vector<double>>()[0],
                                                            marker_in_world["orientation"].as<std::vector<double>>()[1],
                                                            marker_in_world["orientation"].as<std::vector<double>>()[2],
                                                            marker_in_world["orientation"].as<std::vector<double>>()[3])
                                                .normalize(),
                                            tf2::Vector3(marker_in_world["position"].as<std::vector<double>>()[0],
                                                         marker_in_world["position"].as<std::vector<double>>()[1],
                                                         marker_in_world["position"].as<std::vector<double>>()[2]));

    // Pose of marker in camera frame according to detection
    // Detected transform considers opposite order base vectors, so we need to apply correction
    auto T_marker_in_camera_raw = tf2::Transform(
        tf2::Quaternion(m.pose.orientation.x, m.pose.orientation.y, m.pose.orientation.z, m.pose.orientation.w)
            .normalize(),
        tf2::Vector3(m.pose.position.x, m.pose.position.y, m.pose.position.z));
    auto T_marker_in_camera = T_correction_marker_in_camera * T_marker_in_camera_raw;
    T_marker_in_camera.setRotation(T_marker_in_camera.getRotation().normalize());
    // Publishing TF of detected marker relative to camera frame
    geometry_msgs::msg::TransformStamped ts_marker;
    ts_marker.header.stamp = this->get_clock()->now();
    ts_marker.header.frame_id = this->get_parameter("aruco_camera_frame").as_string();
    ts_marker.child_frame_id = "aruco_marker_" + key;
    ts_marker.transform = tf2::toMsg(T_marker_in_camera);
    this->tf_broadcaster->sendTransform(ts_marker);

    // Pose of camera in world frame according to current marker's detection
    auto T_camera_in_world = T_marker_in_world * T_marker_in_camera.inverse();
    T_camera_in_world.setRotation(T_camera_in_world.getRotation().normalize());

    // Add pose candidate of camera in world frame
    poses_camera_in_world.push_back(T_camera_in_world);
  }
  if (poses_camera_in_world.empty())
  {
    RCLCPP_WARN(this->get_logger(), "No valid markers processed, no TF published.");
    return;
  }
  // ++++++ End section of collecting camera pose candidates in world frame into a vector ++++++ //

  // ++++++ Section of averaging all previously obtained camera pose estimations ++++++ //
  // Average all obtained camera pose estimations in world frame
  tf2::Vector3 avg_translation = poses_camera_in_world[0].getOrigin();
  tf2::Quaternion avg_rotation = poses_camera_in_world[0].getRotation();
  for (size_t i = 1; i < poses_camera_in_world.size(); ++i)
  {
    avg_translation += poses_camera_in_world[i].getOrigin();
    tf2::Quaternion q = poses_camera_in_world[i].getRotation();
    if (avg_rotation.dot(q) < 0)
    {
      q = tf2::Quaternion(-q.x(), -q.y(), -q.z(), -q.w());
    }
    double t = 1.0 / static_cast<double>(i + 1);
    avg_rotation = avg_rotation.slerp(q, t);
  }
  avg_translation /= static_cast<double>(poses_camera_in_world.size());
  avg_rotation.normalize();
  // Check for NaNs
  if (std::isnan(avg_translation.x()) || std::isnan(avg_rotation.w()))
  {
    RCLCPP_ERROR(this->get_logger(), "NaN detected in transform math! Skipping publish.");
    return;
  }
  if (avg_rotation.length2() > 1e-6)
  {
    avg_rotation.normalize();
  }
  else
  {
    avg_rotation.setValue(0, 0, 0, 1);
  }
  auto T_camera_in_world_avg = tf2::Transform(avg_rotation, avg_translation);
  T_camera_in_world_avg.setRotation(T_camera_in_world_avg.getRotation().normalize());
  // ++++++ End section of averaging all previously obtained camera pose estimations ++++++ //

  // ++++++ Section of calculating and publishing transform to map in world frame ++++++ //
  string map_ns_sl = (this->get_parameter("map_namespace").as_string() == "") ?
                         "" :
                         this->get_parameter("map_namespace").as_string() + "/";
  string map_frame = map_ns_sl + "map";
  // Only for mapper robot in order to calculate tf between its map frame and marker map's world frame
  if (this->get_parameter("is_mapper").as_bool())
  {
    try
    {
      // Calculating world to map transform
      tf2::Transform T_camera_in_map;
      tf2::fromMsg(this->tf_buffer
                       ->lookupTransform(map_frame, this->get_parameter("aruco_camera_frame").as_string(),
                                         tf2::TimePointZero  // rclcpp::Duration::from_seconds(1.0)
                                         )
                       .transform,
                   T_camera_in_map);
      T_camera_in_map.setRotation(T_camera_in_map.getRotation().normalize());
      auto T_map_in_world = T_camera_in_world_avg * T_camera_in_map.inverse();
      T_map_in_world.setRotation(T_map_in_world.getRotation().normalize());
      // Publishing TF of map in world frame
      geometry_msgs::msg::TransformStamped ts_map_in_world;
      ts_map_in_world.header.stamp = this->get_clock()->now();
      ts_map_in_world.header.frame_id = this->get_parameter("aruco_world_frame").as_string();
      ts_map_in_world.child_frame_id = map_frame;
      ts_map_in_world.transform = tf2::toMsg(T_map_in_world);
      this->tf_broadcaster->sendTransform(ts_map_in_world);
    }
    catch (exception& e)
    {
      RCLCPP_WARN(this->get_logger(), "Could not get %s to %s transform: %s",
                  this->get_parameter("aruco_world_frame").as_string(), map_frame, e.what());
      return;
    }
    // ++++++ End section of calculating and publishing transform to map in world frame ++++++ //

    return;
  }

  // ++++++ Section of calculating and publishing initialpose for localization (base_footprint in map frame) ++++++ //
  // Only for localizer robot in order to calculate tf between robot's base and mapper robot's map frame
  try
  {
    // Getting map in world transform from mapper robot
    tf2::Transform T_map_in_world;
    tf2::fromMsg(
        this->tf_buffer_aruco
            ->lookupTransform(this->get_parameter("aruco_world_frame").as_string(), map_frame, tf2::TimePointZero)
            .transform,
        T_map_in_world);
    T_map_in_world.setRotation(T_map_in_world.getRotation().normalize());
    // Publishing TF of map in world frame only for monitoring purposes
    geometry_msgs::msg::TransformStamped ts_map_in_world;
    ts_map_in_world.header.stamp = msg.header.stamp;
    ts_map_in_world.header.frame_id = this->get_parameter("aruco_world_frame").as_string();
    ts_map_in_world.child_frame_id = map_frame;
    ts_map_in_world.transform = tf2::toMsg(T_map_in_world);
    this->tf_broadcaster->sendTransform(ts_map_in_world);
    // Calculating world to map transform
    tf2::Transform T_base_in_camera;
    tf2::fromMsg(this->tf_buffer
                     ->lookupTransform(this->get_parameter("aruco_camera_frame").as_string(),
                                       this->get_parameter("base_frame").as_string(), tf2::TimePointZero)
                     .transform,
                 T_base_in_camera);
    T_base_in_camera.setRotation(T_base_in_camera.getRotation().normalize());
    auto T_base_in_map = T_map_in_world.inverse() * T_camera_in_world_avg * T_base_in_camera;
    T_base_in_map.setRotation(T_base_in_map.getRotation().normalize());
    // Publishing initialpose (estimated base_footprint in map frame)
    auto t_base_in_map = tf2::toMsg(T_base_in_map);
    geometry_msgs::msg::PoseWithCovarianceStamped pwcs_base_in_map;
    pwcs_base_in_map.header.stamp = msg.header.stamp;
    pwcs_base_in_map.header.frame_id = map_frame;
    pwcs_base_in_map.pose.pose.position.x = t_base_in_map.translation.x;
    pwcs_base_in_map.pose.pose.position.y = t_base_in_map.translation.y;
    pwcs_base_in_map.pose.pose.position.z = t_base_in_map.translation.z;
    pwcs_base_in_map.pose.pose.orientation.x = t_base_in_map.rotation.x;
    pwcs_base_in_map.pose.pose.orientation.y = t_base_in_map.rotation.y;
    pwcs_base_in_map.pose.pose.orientation.z = t_base_in_map.rotation.z;
    pwcs_base_in_map.pose.pose.orientation.w = t_base_in_map.rotation.w;
    // Making a diagonal matrix for covariance
    std::array<double, 36UL> cov_mx;
    cov_mx[0] = 0.05;
    cov_mx[7] = 0.05;
    cov_mx[14] = 0.05;
    cov_mx[21] = 0.01;
    cov_mx[28] = 0.01;
    cov_mx[35] = 0.01;
    pwcs_base_in_map.pose.covariance = cov_mx;
    this->initialpose_pub->publish(pwcs_base_in_map);
    // update last time of /initialpose topic publish
    this->last_initialpose_publish_time = this->get_clock()->now();
  }
  catch (exception& e)
  {
    RCLCPP_WARN(this->get_logger(), "Could not get %s to %s transform: %s",
                this->get_parameter("base_frame").as_string(), map_frame, e.what());
    return;
  }
  return;
  // ++++++ End section of calculating and publishing initialpose for localization (base_footprint in map frame) ++++++
  // //
}