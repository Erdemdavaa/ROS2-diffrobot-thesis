#include <../include/ArucoLocalizer.h>
#include <memory>

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  auto aruco_localizer = std::make_shared<ArucoLocalizer>();
  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(aruco_localizer);
  executor.add_node(aruco_localizer->get_inner_node_tf_listener_aruco());
  executor.spin();
  rclcpp::shutdown();
  return 0;
}