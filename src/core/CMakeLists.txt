file(GLOB_RECURSE SOURCES "*.cpp")
pybind11_add_module(core ${SOURCES})
target_link_libraries(core PRIVATE ${SHAPELIB_LIBRARY} ${STD_FILESYSTEM})
