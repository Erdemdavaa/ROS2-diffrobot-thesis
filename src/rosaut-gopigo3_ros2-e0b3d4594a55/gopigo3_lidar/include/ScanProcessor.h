#pragma once

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/laser_scan.hpp>

class ScanProcessor : public rclcpp::Node
{
public:
  ScanProcessor();

private:
  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr raw_sub;
  rclcpp::Publisher<sensor_msgs::msg::LaserScan>::SharedPtr filtered_pub;

  void scan_callback(const sensor_msgs::msg::LaserScan::SharedPtr msg);

  void filter(sensor_msgs::msg::LaserScan* scan);
};