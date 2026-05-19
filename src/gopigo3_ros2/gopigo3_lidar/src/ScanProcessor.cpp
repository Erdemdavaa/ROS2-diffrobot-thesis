#include <../include/ScanProcessor.h>

using std::placeholders::_1;
using namespace std;

ScanProcessor::ScanProcessor() : Node("scan_processor")
{
  this->declare_parameter("scan_raw_topic_name", "/scan");
  this->declare_parameter("scan_processed_topic_name", "/scan_processed");

  filtered_pub = this->create_publisher<sensor_msgs::msg::LaserScan>(
      this->get_parameter("scan_processed_topic_name").as_string(), 10);
  raw_sub = this->create_subscription<sensor_msgs::msg::LaserScan>(
      this->get_parameter("scan_raw_topic_name").as_string(), 10, std::bind(&ScanProcessor::scan_callback, this, _1));
}

void ScanProcessor::scan_callback(const sensor_msgs::msg::LaserScan::SharedPtr msg)
{
  sensor_msgs::msg::LaserScan local_scan = *msg;
  filter(&local_scan);
  filtered_pub->publish(local_scan);
}

void ScanProcessor::filter(sensor_msgs::msg::LaserScan* scan)
{
  // This example filters out a continuous range of lidar scan points
  // Filtered range lasts filtered_angle_min to filtered_angle_max considering front of the robot as zero angle
  double angle_res = scan->angle_increment;
  size_t scan_size = scan->ranges.size();
  double filtered_angle_min = scan->angle_min;
  double filtered_angle_max = scan->angle_min + M_PI / 18;  // 10°
  size_t i_min = (filtered_angle_min - scan->angle_min) / angle_res;
  size_t i_max = (filtered_angle_max - scan->angle_min) / angle_res;
  for (size_t i = 0; i < scan_size; i++)
  {
    if (scan->ranges[i] < 5.0 && i >= i_min && i <= i_max)
    {
      scan->ranges[i] = scan->range_max;
    }
  }
}