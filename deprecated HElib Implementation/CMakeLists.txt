cmake_minimum_required(VERSION 3.16)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

project(Main)

find_package(helib)
find_package(Arrow REQUIRED)

add_executable(main main.cpp)
target_link_libraries(main PRIVATE helib)
target_link_libraries(main PRIVATE Arrow::arrow_shared)