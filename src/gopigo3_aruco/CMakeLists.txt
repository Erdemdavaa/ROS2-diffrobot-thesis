cmake_minimum_required(VERSION 3.8)
project(gopigo3_aruco)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)
find_package(rclcpp REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(aruco_opencv_msgs REQUIRED)
find_package(yaml-cpp REQUIRED)


add_executable(aruco_localizer src/aruco_localizer.cpp src/ArucoLocalizer.cpp)
target_include_directories(aruco_localizer PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
target_compile_features(aruco_localizer PUBLIC c_std_99 cxx_std_17)  # Require C99 and C++17
ament_target_dependencies(aruco_localizer rclcpp sensor_msgs aruco_opencv_msgs tf2 tf2_ros tf2_geometry_msgs yaml-cpp)
target_link_libraries(aruco_localizer yaml-cpp)
target_compile_definitions(aruco_localizer PRIVATE _GLIBCXX_USE_CXX11_ABI=1)

if(BUILD_TESTING)
find_package(ament_lint_auto REQUIRED)
# the following line skips the linter which checks for copyrights
# comment the line when a copyright and license is added to all source files
set(ament_cmake_copyright_FOUND TRUE)
# the following line skips cpplint (only works in a git repo)
# comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
  endif()
  
install(TARGETS aruco_localizer
  DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch markers
  DESTINATION share/${PROJECT_NAME})

ament_package()
