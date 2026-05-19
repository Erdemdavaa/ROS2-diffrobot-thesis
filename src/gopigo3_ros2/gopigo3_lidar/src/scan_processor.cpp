#include <../include/ScanProcessor.h>
#include <memory>

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  auto scan_proc = std::make_shared<ScanProcessor>();
  rclcpp::spin(scan_proc);
  rclcpp::shutdown();
  return 0;
}