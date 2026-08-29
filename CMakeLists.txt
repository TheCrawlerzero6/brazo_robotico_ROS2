cmake_minimum_required(VERSION 3.8)
project(bajana_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY
    config
    launch
    rviz
    urdf
    worlds
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS
    scripts/joint_sequence_controller.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
