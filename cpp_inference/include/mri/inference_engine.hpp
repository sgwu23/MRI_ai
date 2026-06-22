#pragma once

#include <cstdint>
#include <memory>
#include <string>
#include <vector>

namespace mri {

struct TensorShape {
    std::vector<std::int64_t> dims;
    std::size_t element_count{0U};
};

struct InferenceResult {
    std::vector<std::uint8_t> dicom_bytes;
    float latency_ms{0.0F};
    std::string backend{"stub"};
    bool ok{false};
    std::string message;
    TensorShape output_shape;
};

class InferenceBackend {
public:
    virtual ~InferenceBackend() = default;

    [[nodiscard]] virtual bool available() const noexcept = 0;
    [[nodiscard]] virtual InferenceResult run(const std::vector<std::uint8_t>& input_bytes) const = 0;
};

#ifdef MRI_ENABLE_TENSORRT
[[nodiscard]] std::unique_ptr<InferenceBackend> create_tensorrt_backend(const std::string& engine_path);
#endif

class InferenceEngine {
public:
    explicit InferenceEngine(std::string model_path);
    ~InferenceEngine();

    InferenceEngine(const InferenceEngine&) = delete;
    InferenceEngine& operator=(const InferenceEngine&) = delete;
    InferenceEngine(InferenceEngine&&) noexcept;
    InferenceEngine& operator=(InferenceEngine&&) noexcept;

    [[nodiscard]] const std::string& model_path() const noexcept;
    [[nodiscard]] bool is_accelerated() const noexcept;
    [[nodiscard]] InferenceResult run(const std::vector<std::uint8_t>& input_dicom) const;

private:
    std::string model_path_;
    std::unique_ptr<InferenceBackend> backend_;
};

}  // namespace mri
