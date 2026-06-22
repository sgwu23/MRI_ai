#include "mri/inference_engine.hpp"

#include <exception>
#include <utility>

namespace mri {

InferenceEngine::InferenceEngine(std::string model_path) : model_path_(std::move(model_path)) {
#ifdef MRI_ENABLE_TENSORRT
    try {
        backend_ = create_tensorrt_backend(model_path_);
    } catch (const std::exception&) {
        backend_.reset();
    }
#endif
}

InferenceEngine::~InferenceEngine() = default;
InferenceEngine::InferenceEngine(InferenceEngine&&) noexcept = default;
InferenceEngine& InferenceEngine::operator=(InferenceEngine&&) noexcept = default;

const std::string& InferenceEngine::model_path() const noexcept {
    return model_path_;
}

bool InferenceEngine::is_accelerated() const noexcept {
    return backend_ != nullptr && backend_->available();
}

InferenceResult InferenceEngine::run(const std::vector<std::uint8_t>& input_dicom) const {
    if (is_accelerated()) {
        return backend_->run(input_dicom);
    }

    InferenceResult result;
    if (input_dicom.empty()) {
        result.ok = false;
        result.message = "empty input";
        return result;
    }

    result.dicom_bytes = input_dicom;
    result.latency_ms = 0.0F;
    result.backend = "host-stub";
    result.ok = true;
    result.message = "host stub echoes DICOM bytes; TensorRT backend requires Jetson";
    result.output_shape.dims = {static_cast<std::int64_t>(result.dicom_bytes.size())};
    result.output_shape.element_count = result.dicom_bytes.size();
    return result;
}

}  // namespace mri
