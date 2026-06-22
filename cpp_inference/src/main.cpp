#include "mri/inference_engine.hpp"

#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

namespace {

std::vector<std::uint8_t> read_binary_or_zero(const std::string& path) {
    if (path.empty() || path == "-") {
        std::vector<float> zero_input(128U * 128U, 0.0F);
        return std::vector<std::uint8_t>(zero_input.size() * sizeof(float));
    }

    std::ifstream file(path, std::ios::binary);
    if (!file) {
        throw std::runtime_error("failed to open input tensor: " + path);
    }
    file.seekg(0, std::ios::end);
    const auto size = file.tellg();
    file.seekg(0, std::ios::beg);
    std::vector<std::uint8_t> bytes(static_cast<std::size_t>(size));
    file.read(reinterpret_cast<char*>(bytes.data()), size);
    return bytes;
}

void write_binary(const std::string& path, const std::vector<std::uint8_t>& bytes) {
    if (path.empty() || path == "-") {
        return;
    }

    std::ofstream file(path, std::ios::binary);
    if (!file) {
        throw std::runtime_error("failed to open output tensor: " + path);
    }
    file.write(reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
}

}  // namespace

int main(int argc, char** argv) {
    const std::string model_path = argc > 1 ? argv[1] : "models/recon.onnx";
    const int repeats = argc > 2 ? std::max(1, std::atoi(argv[2])) : 20;
    const int warmup = argc > 3 ? std::max(0, std::atoi(argv[3])) : 3;
    const std::string input_path = argc > 4 ? argv[4] : "-";
    const std::string output_path = argc > 5 ? argv[5] : "-";
    const mri::InferenceEngine engine{model_path};

    std::vector<std::uint8_t> input_bytes;
    try {
        input_bytes = read_binary_or_zero(input_path);
    } catch (const std::exception& error) {
        std::cerr << error.what() << "\n";
        return 1;
    }

    for (int index = 0; index < warmup; ++index) {
        const auto warmup_result = engine.run(input_bytes);
        if (!warmup_result.ok) {
            std::cerr << "warmup failed: " << warmup_result.message << "\n";
            return 1;
        }
    }

    mri::InferenceResult result;
    float total_latency_ms = 0.0F;
    float min_latency_ms = std::numeric_limits<float>::max();
    float max_latency_ms = 0.0F;
    for (int index = 0; index < repeats; ++index) {
        result = engine.run(input_bytes);
        if (!result.ok) {
            std::cerr << "inference failed: " << result.message << "\n";
            return 1;
        }
        total_latency_ms += result.latency_ms;
        min_latency_ms = std::min(min_latency_ms, result.latency_ms);
        max_latency_ms = std::max(max_latency_ms, result.latency_ms);
    }

    try {
        write_binary(output_path, result.dicom_bytes);
    } catch (const std::exception& error) {
        std::cerr << error.what() << "\n";
        return 1;
    }

    std::cout << "backend=" << result.backend << "\n";
    std::cout << "accelerated=" << engine.is_accelerated() << "\n";
    std::cout << "ok=" << result.ok << "\n";
    std::cout << "bytes=" << result.dicom_bytes.size() << "\n";
    std::cout << "warmup=" << warmup << "\n";
    std::cout << "repeats=" << repeats << "\n";
    std::cout << "input_path=" << input_path << "\n";
    std::cout << "output_path=" << output_path << "\n";
    std::cout << "latency_ms_last=" << result.latency_ms << "\n";
    std::cout << "latency_ms_mean=" << total_latency_ms / static_cast<float>(repeats) << "\n";
    std::cout << "latency_ms_min=" << min_latency_ms << "\n";
    std::cout << "latency_ms_max=" << max_latency_ms << "\n";
    std::cout << "output_elements=" << result.output_shape.element_count << "\n";
    std::cout << "message=" << result.message << "\n";
    return result.ok ? 0 : 1;
}
