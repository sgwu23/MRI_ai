#include "mri/inference_engine.hpp"

#ifdef MRI_ENABLE_TENSORRT

#include <NvInfer.h>
#include <cuda_runtime_api.h>

#include <algorithm>
#include <chrono>
#include <cstring>
#include <fstream>
#include <iostream>
#include <numeric>
#include <stdexcept>

namespace mri {

namespace {

class TrtLogger final : public nvinfer1::ILogger {
public:
    void log(Severity severity, const char* msg) noexcept override {
        if (severity <= Severity::kWARNING) {
            std::cerr << "[TensorRT] " << msg << '\n';
        }
    }
};

TrtLogger g_logger;

void check_cuda(cudaError_t status, const char* operation) {
    if (status != cudaSuccess) {
        throw std::runtime_error(std::string(operation) + ": " + cudaGetErrorString(status));
    }
}

std::vector<char> read_binary_file(const std::string& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) {
        throw std::runtime_error("failed to open TensorRT engine: " + path);
    }

    file.seekg(0, std::ios::end);
    const auto size = file.tellg();
    file.seekg(0, std::ios::beg);

    std::vector<char> bytes(static_cast<std::size_t>(size));
    file.read(bytes.data(), size);
    return bytes;
}

std::size_t volume(const nvinfer1::Dims& dims) {
    std::size_t result = 1U;
    for (int32_t index = 0; index < dims.nbDims; ++index) {
        result *= static_cast<std::size_t>(dims.d[index]);
    }
    return result;
}

TensorShape to_shape(const nvinfer1::Dims& dims) {
    TensorShape shape;
    shape.dims.reserve(static_cast<std::size_t>(dims.nbDims));
    for (int32_t index = 0; index < dims.nbDims; ++index) {
        shape.dims.push_back(dims.d[index]);
    }
    shape.element_count = volume(dims);
    return shape;
}

}  // namespace

class TensorRtBackend final : public InferenceBackend {
public:
    explicit TensorRtBackend(const std::string& engine_path) {
        const auto engine_bytes = read_binary_file(engine_path);
        runtime_.reset(nvinfer1::createInferRuntime(g_logger));
        if (!runtime_) {
            throw std::runtime_error("failed to create TensorRT runtime");
        }

        engine_.reset(runtime_->deserializeCudaEngine(engine_bytes.data(), engine_bytes.size()));
        if (!engine_) {
            throw std::runtime_error("failed to deserialize TensorRT engine");
        }

        context_.reset(engine_->createExecutionContext());
        if (!context_) {
            throw std::runtime_error("failed to create TensorRT execution context");
        }

        discover_tensors();
        allocate_buffers();
        check_cuda(cudaStreamCreate(&stream_), "cudaStreamCreate");
    }

    ~TensorRtBackend() override {
        if (stream_ != nullptr) {
            cudaStreamDestroy(stream_);
        }
        if (input_device_ != nullptr) {
            cudaFree(input_device_);
        }
        if (output_device_ != nullptr) {
            cudaFree(output_device_);
        }
    }

    TensorRtBackend(const TensorRtBackend&) = delete;
    TensorRtBackend& operator=(const TensorRtBackend&) = delete;

    [[nodiscard]] bool available() const noexcept override {
        return engine_ != nullptr && context_ != nullptr;
    }

    [[nodiscard]] InferenceResult run(const std::vector<std::uint8_t>& input_bytes) const override {
        InferenceResult result;
        result.backend = "tensorrt-fp16";
        result.output_shape = to_shape(output_dims_);

        std::fill(input_host_.begin(), input_host_.end(), 0.0F);
        const auto input_float_bytes = input_host_.size() * sizeof(float);
        if (!input_bytes.empty()) {
            std::memcpy(input_host_.data(), input_bytes.data(), std::min(input_bytes.size(), input_float_bytes));
        }

        const auto start = std::chrono::steady_clock::now();

        check_cuda(
            cudaMemcpyAsync(input_device_, input_host_.data(), input_float_bytes, cudaMemcpyHostToDevice, stream_),
            "cudaMemcpyAsync H2D");
        if (!context_->setTensorAddress(input_name_.c_str(), input_device_)) {
            throw std::runtime_error("failed to bind TensorRT input tensor");
        }
        if (!context_->setTensorAddress(output_name_.c_str(), output_device_)) {
            throw std::runtime_error("failed to bind TensorRT output tensor");
        }
        if (!context_->enqueueV3(stream_)) {
            throw std::runtime_error("TensorRT enqueueV3 failed");
        }
        check_cuda(
            cudaMemcpyAsync(
                output_host_.data(),
                output_device_,
                output_host_.size() * sizeof(float),
                cudaMemcpyDeviceToHost,
                stream_),
            "cudaMemcpyAsync D2H");
        check_cuda(cudaStreamSynchronize(stream_), "cudaStreamSynchronize");

        const auto end = std::chrono::steady_clock::now();
        result.latency_ms = std::chrono::duration<float, std::milli>(end - start).count();
        result.dicom_bytes.resize(output_host_.size() * sizeof(float));
        std::memcpy(result.dicom_bytes.data(), output_host_.data(), result.dicom_bytes.size());
        result.ok = true;
        result.message = "TensorRT engine inference completed";
        return result;
    }

private:
    struct RuntimeDeleter {
        void operator()(nvinfer1::IRuntime* ptr) const {
            delete ptr;
        }
    };

    struct EngineDeleter {
        void operator()(nvinfer1::ICudaEngine* ptr) const {
            delete ptr;
        }
    };

    struct ContextDeleter {
        void operator()(nvinfer1::IExecutionContext* ptr) const {
            delete ptr;
        }
    };

    void discover_tensors() {
        for (int32_t index = 0; index < engine_->getNbIOTensors(); ++index) {
            const char* name = engine_->getIOTensorName(index);
            const auto mode = engine_->getTensorIOMode(name);
            if (mode == nvinfer1::TensorIOMode::kINPUT) {
                input_name_ = name;
                input_dims_ = engine_->getTensorShape(name);
            } else if (mode == nvinfer1::TensorIOMode::kOUTPUT) {
                output_name_ = name;
                output_dims_ = engine_->getTensorShape(name);
            }
        }

        if (input_name_.empty() || output_name_.empty()) {
            throw std::runtime_error("TensorRT engine must have one input and one output");
        }
        input_elements_ = volume(input_dims_);
        output_elements_ = volume(output_dims_);
    }

    void allocate_buffers() {
        check_cuda(cudaMalloc(&input_device_, input_elements_ * sizeof(float)), "cudaMalloc input");
        check_cuda(cudaMalloc(&output_device_, output_elements_ * sizeof(float)), "cudaMalloc output");
        input_host_.assign(input_elements_, 0.0F);
        output_host_.assign(output_elements_, 0.0F);
    }

    std::unique_ptr<nvinfer1::IRuntime, RuntimeDeleter> runtime_;
    std::unique_ptr<nvinfer1::ICudaEngine, EngineDeleter> engine_;
    std::unique_ptr<nvinfer1::IExecutionContext, ContextDeleter> context_;
    std::string input_name_;
    std::string output_name_;
    nvinfer1::Dims input_dims_{};
    nvinfer1::Dims output_dims_{};
    std::size_t input_elements_{0U};
    std::size_t output_elements_{0U};
    void* input_device_{nullptr};
    void* output_device_{nullptr};
    cudaStream_t stream_{nullptr};
    mutable std::vector<float> input_host_;
    mutable std::vector<float> output_host_;
};

std::unique_ptr<InferenceBackend> create_tensorrt_backend(const std::string& engine_path) {
    return std::make_unique<TensorRtBackend>(engine_path);
}

}  // namespace mri

#endif  // MRI_ENABLE_TENSORRT
