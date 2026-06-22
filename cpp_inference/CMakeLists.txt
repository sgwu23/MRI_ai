cmake_minimum_required(VERSION 3.20)

project(mri_edge_inference LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(MRI_ENABLE_TENSORRT "Build TensorRT backend" OFF)

add_library(mri_inference
    src/inference_engine.cpp
)

target_include_directories(mri_inference PUBLIC include)

if(MRI_ENABLE_TENSORRT)
    find_library(NVINFER_LIB nvinfer
        HINTS /usr/lib/aarch64-linux-gnu
        REQUIRED
    )
    find_library(CUDART_LIB cudart
        HINTS /usr/local/cuda/lib64 /usr/local/cuda/targets/aarch64-linux/lib /usr/local/cuda-12.6/targets/aarch64-linux/lib
        REQUIRED
    )

    target_sources(mri_inference PRIVATE
        src/tensorrt_backend.cpp
    )

    target_compile_definitions(mri_inference PUBLIC MRI_ENABLE_TENSORRT=1)
    target_include_directories(mri_inference PRIVATE
        /usr/local/cuda/include
        /usr/local/cuda-12.6/targets/aarch64-linux/include
    )
    target_link_libraries(mri_inference PRIVATE ${NVINFER_LIB} ${CUDART_LIB})
endif()

add_executable(mri_inference_demo
    src/main.cpp
)

target_link_libraries(mri_inference_demo PRIVATE mri_inference)
