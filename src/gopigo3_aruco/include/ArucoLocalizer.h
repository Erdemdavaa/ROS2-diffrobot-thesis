#pragma once

#include <rclcpp/rclcpp.hpp>
#include <aruco_opencv_msgs/msg/aruco_detection.hpp>
#include <tf2_ros/buffer.hpp>
#include <tf2_ros/transform_broadcaster.hpp>
#include <tf2_ros/transform_listener.hpp>
#include <geometry_msgs/msg/pose_with_covariance_stamped.hpp>

class ArucoLocalizer : public rclcpp::Node
{
public:
  ArucoLocalizer();

  std::shared_ptr<rclcpp::Node> get_inner_node_tf_listener_aruco() const
  {
    return this->inner_node_tf_listener_aruco;
  }

private:
  tf2::Transform T_correction_marker_in_camera;
  std::unique_ptr<tf2_ros::Buffer> tf_buffer;
  std::shared_ptr<tf2_ros::TransformListener> tf_listener;
  std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster;
  std::unique_ptr<tf2_ros::Buffer> tf_buffer_aruco;
  std::shared_ptr<tf2_ros::TransformListener> tf_listener_aruco;
  rclcpp::Publisher<geometry_msgs::msg::PoseWithCovarianceStamped>::SharedPtr initialpose_pub;
  rclcpp::Subscription<aruco_opencv_msgs::msg::ArucoDetection>::SharedPtr aruco_sub;
  void aruco_detection_callback(const aruco_opencv_msgs::msg::ArucoDetection msg);

  rclcpp::Time last_initialpose_publish_time;
  rclcpp::Time last_processing_time;
  std::shared_ptr<rclcpp::Node> inner_node_tf_listener_aruco;
};