# 项目技术走读：MRI Edge RTOS AI

这份文档用于你熟悉项目和准备面试。它按项目阶段解释：这个阶段解决什么问题、写了哪些代码或脚本、脚本大致怎么工作、输入输出是什么、面试时应该怎么讲。

## 0. 项目一句话

这是一个 MRI 风格的嵌入式医疗影像原型项目：用 fastMRI 数据训练轻量 U-Net 做欠采样 MRI 重建，把 PyTorch 模型导出到 ONNX，再在 Jetson Orin 上通过 TensorRT FP16 加速推理，同时保留 C++ 推理服务边界和 Zephyr RTOS/STM32 控制侧脚手架。

项目当前完成的是 AI 重建与 Jetson 部署闭环。STM32 + RTOS 控制侧是下一阶段。

## 1. 系统分层

核心模块如下：

```text
fastMRI HDF5 dataset
  -> Python preprocessing and training
  -> PyTorch checkpoint .pth
  -> ONNX export .onnx
  -> TensorRT engine .engine on Jetson
  -> C++ inference service smoke test
  -> benchmark reports and visualization
```

仓库中的主要目录：

- `ai_recon/`: 模型、训练、ONNX 导出、可视化脚本。
- `cpp_inference/`: C++17 推理接口和 TensorRT 后端。
- `firmware/`: Zephyr RTOS 控制侧脚手架。
- `docs/performance/`: 训练和部署结果。
- `docs/assets/`: 重建可视化图片。
- `tests/`: 本地单元测试和 smoke tests。

## 2. 阶段一：基础 MRI 重建链路

目标：先在不训练深度模型的情况下，把“k-space 到图像”的基础链路跑通。

相关代码：

- `ai_recon/src/mri_recon/zero_filled.py`
- `ai_recon/src/mri_recon/masks.py`
- `ai_recon/src/mri_recon/metrics.py`
- `ai_recon/src/mri_recon/phantom.py`
- `ai_recon/scripts/baseline_report.py`

关键概念：

- MRI 原始采集数据在频域，通常叫 k-space。
- 欠采样会减少采集时间，但会带来伪影。
- zero-filled reconstruction 是最基础 baseline：未采样位置填 0，再做 inverse FFT 得到图像。
- PSNR 用来衡量重建图像和目标图像的差异。

脚本产出：

- `docs/performance/baseline_local.md`
- 本地 smoke test 用于确认 FFT、mask、metric 这些基础函数没坏。

面试讲法：

> 我先实现了传统 MRI 重建 baseline，把欠采样 k-space 通过 zero-filled inverse FFT 转成图像，并用 PSNR 做指标。这一步不是为了追求效果，而是为了建立后续深度模型训练的对照组和测试基线。

## 3. 阶段二：轻量 U-Net 模型

目标：用一个小型 residual U-Net 学习从 zero-filled 图像到 target 图像的映射。

相关代码：

- `ai_recon/src/mri_recon/models.py`
- `ai_recon/scripts/train_unet.py`
- `ai_recon/scripts/train_fastmri_unet.py`

模型结构：

- 输入：`1xHxW` 的 zero-filled 图像。
- 输出：`1xHxW` 的重建图像。
- 模型是 residual 形式：`return x + self.out(d1)`。
- 这样模型学的是“修正量”，不是从零生成整张图。

为什么用轻量模型：

- 项目重点是端到端工程闭环，不是刷榜。
- 轻量模型更适合 Jetson 部署和 TensorRT smoke test。
- 训练时间和算力有限，模型需要能快速迭代。

面试讲法：

> 我没有直接上很大的重建网络，而是先用轻量 residual U-Net 完成可部署闭环。它的输入是 zero-filled 图像，输出是残差修正后的重建图。这样可以在有限训练成本下验证数据、训练、导出和边缘推理全链路。

## 4. 阶段三：fastMRI 正式训练

目标：用真实 fastMRI knee single-coil 数据训练正式 v1 模型。

核心脚本：

- `ai_recon/scripts/train_fastmri_unet.py`

输入：

- `--train-root`: fastMRI train HDF5 目录。
- `--val-root`: fastMRI val HDF5 目录。
- `--max-train-slices`: 训练 slice 数。
- `--max-val-slices`: 验证 slice 数。
- `--crop-size`: 图像裁剪尺寸，正式版本为 `320`。
- `--acceleration`: 欠采样倍率，正式版本为 `4`。
- `--amp`: 使用混合精度训练。

输出：

- `outputs/models/unet_fastmri_v1_best.pth`
- `outputs/models/unet_fastmri_v1_last.pth`
- `outputs/logs/fastmri_v1_training.log`
- `docs/performance/fastmri_v1_eval.md`

脚本内部做了什么：

1. 扫描 HDF5 文件，建立 `(file_path, slice_index)` 索引。
2. 从每个 slice 读取 `kspace`。
3. 如果 HDF5 中有 `reconstruction_rss` 或 `reconstruction_esc`，作为 target。
4. 对 k-space 做 4x 欠采样 mask。
5. inverse FFT 得到 zero-filled 图像。
6. center crop 到 `320x320`。
7. 归一化到 `[0, 1]`。
8. 用 U-Net 训练 L1 loss。
9. 每个 epoch 在验证集计算 L1、model PSNR、zero-filled PSNR。
10. 保存 best checkpoint 和 last checkpoint。

正式结果：

- Train slices: `10000`
- Validation slices: `1000`
- Best model PSNR: `26.49 dB`
- Zero-filled PSNR: `22.87 dB`
- PSNR gain: `+3.62 dB`

面试讲法：

> 我把 fastMRI 的 HDF5 文件按 slice 建索引，并在训练时动态生成 4x undersampling mask。训练时输入是 zero-filled 图像，target 是 fastMRI 提供的重建图。最终在 1000 个 validation slices 上，模型从 zero-filled 的 22.87 dB 提升到 26.49 dB。

## 5. 阶段四：ONNX 导出

目标：把 PyTorch checkpoint 转成跨框架部署格式 ONNX。

核心脚本：

- `ai_recon/scripts/export_onnx.py`

典型命令：

```powershell
python ai_recon/scripts/export_onnx.py `
  --checkpoint outputs/models/unet_fastmri_v1_best.pth `
  --output outputs/models/unet_fastmri_v1_best.onnx
```

脚本内部做了什么：

1. 加载 `build_unet()`，构造和训练时一致的网络。
2. `torch.load()` 读取 `.pth` checkpoint。
3. 从 checkpoint 中取出 `state["model"]` 加载权重。
4. 从 checkpoint 的 `config` 里读取 `crop_size`，默认 `320`。
5. 构造一个 dummy input：`torch.zeros((1, 1, 320, 320))`。
6. 调用 `torch.onnx.export()` 导出模型。
7. 设置输入名为 `masked_image`，输出名为 `reconstruction`。

为什么需要 dummy input：

- ONNX 导出需要沿着一次前向计算 trace 模型图。
- dummy input 的 shape 会决定导出图中的输入尺寸。
- 本项目部署时固定使用 `1x1x320x320`，便于 TensorRT 构建静态 shape engine。

Windows 兼容点：

- RunPod/Linux checkpoint 里保存了 `PosixPath`。
- Windows 直接 `torch.load()` 可能报错。
- 脚本中加入了 `pathlib.PosixPath = pathlib.WindowsPath` 兼容处理。

面试讲法：

> ONNX 导出本质上是把训练好的 PyTorch 计算图和权重转成中间表示。我固定了 `1x1x320x320` 输入，这样 TensorRT 可以构建静态优化 engine。脚本会从 checkpoint 读取训练时 crop size，避免训练和部署尺寸不一致。

## 6. 阶段五：TensorRT 部署到 Jetson

目标：在 Jetson Orin 上把 ONNX 编译成 TensorRT FP16 engine，并测量 latency。

核心命令：

```bash
/usr/src/tensorrt/bin/trtexec \
  --onnx=models/unet_fastmri_v1_best.onnx \
  --saveEngine=models/unet_fastmri_v1_best_fp16.engine \
  --fp16 \
  --shapes=masked_image:1x1x320x320 \
  --duration=10
```

输出：

- `models/unet_fastmri_v1_best_fp16.engine`
- `docs/performance/trtexec_fastmri_v1_fp16.log`

结果：

- TensorRT version: `10.3.0`
- Engine size: `0.41238 MiB`
- Throughput: `179.341 qps`
- Host latency mean: `5.65208 ms`
- GPU compute mean: `5.56861 ms`

面试讲法：

> Jetson 部署阶段我使用 TensorRT 的 `trtexec` 将 ONNX 编译成 FP16 engine。输入 shape 固定为 `1x1x320x320`，和 ONNX 导出一致。`trtexec` 的结果用于确认模型可以被 TensorRT 解析、编译，并在 Jetson 上稳定运行。

## 7. 阶段六：C++ TensorRT 推理服务

目标：不只用 `trtexec`，还要证明项目自己的 C++ 代码能加载 engine 并执行推理。

相关代码：

- `cpp_inference/include/mri/inference_engine.hpp`
- `cpp_inference/src/inference_engine.cpp`
- `cpp_inference/src/tensorrt_backend.cpp`
- `cpp_inference/src/main.cpp`

C++ 推理流程：

1. `InferenceEngine` 接收模型路径。
2. 如果开启 `MRI_ENABLE_TENSORRT`，创建 TensorRT backend。
3. TensorRT backend 读取 `.engine` 文件。
4. 创建 `IRuntime`、`ICudaEngine`、`IExecutionContext`。
5. 发现 input/output tensor 名称和 shape。
6. 分配 host/device buffer。
7. 复制输入到 GPU。
8. 通过 `context_->enqueueV3(stream_)` 执行推理。
9. 把输出从 GPU 拷回 host。
10. 返回 latency、output bytes、output shape 等信息。

验证命令：

```bash
./build/jetson-cpp/mri_inference_demo models/unet_fastmri_v1_best_fp16.engine 50 5
```

结果：

- Backend: `tensorrt-fp16`
- Accelerated: `1`
- Output elements: `102400`
- Output bytes: `409600`
- Mean latency: `8.30151 ms`

为什么 C++ latency 比 `trtexec` 高：

- `trtexec` 是高度优化的 benchmark 工具。
- C++ smoke 包含项目自己的输入准备、buffer 管理、计时逻辑。
- 当前 C++ 代码是验证服务边界，不是最终极限优化版本。

面试讲法：

> 我没有只停在 `trtexec`，而是实现了 C++ TensorRT backend。它会反序列化 engine、分配 CUDA buffer、绑定 tensor address，并通过 `enqueueV3` 执行推理。这样证明模型不是只能在工具里跑，而是能嵌入到项目自己的 C++ 服务接口中。

## 8. 阶段七：可视化和结果沉淀

目标：让项目结果可被面试官直观看到。

核心脚本：

- `ai_recon/scripts/make_recon_visualization.py`

输入：

- checkpoint `.pth`
- 可选真实 fastMRI `.h5` 文件
- slice index
- output dir

输出：

- `01_input_kspace.png`
- `02_zero_filled.png`
- `03_model_reconstruction.png`
- `04_target.png`
- `fastmri_v1_reconstruction_contact_sheet.png`
- `README.md`

真实样例目录：

- `docs/assets/fastmri_v1_real/README.md`

脚本内部做了什么：

1. 读取 checkpoint。
2. 如果传入 `.h5`，读取真实 fastMRI slice。
3. 如果没有 `.h5`，生成 synthetic phantom smoke sample。
4. 对 k-space 做 4x undersampling。
5. 生成 zero-filled 图像。
6. 加载 U-Net 并推理。
7. 计算单 slice zero-filled PSNR 和 model PSNR。
8. 写出四张图和 contact sheet。

为什么脚本不用 Matplotlib 也能生成图：

- 为了避免环境问题，脚本内置了一个简单 PNG writer。
- 它用 Python 标准库 `zlib` 和 PNG chunk 格式直接写灰度 RGB PNG。
- 这样在没有 Pillow/Matplotlib 的环境中也可以生成图片。

真实样例结果：

- Zero-filled PSNR: `17.15 dB`
- Model reconstruction PSNR: `17.99 dB`
- Sample gain: `+0.84 dB`

面试讲法：

> 我增加了真实验证样本的可视化，从左到右展示欠采样 k-space、zero-filled、模型重建和 target。这样不仅有总体 PSNR 指标，也能直观看到模型对伪影的抑制效果。

## 9. 当前仓库中的重要产物

建议面试前重点看这些文件：

- `README.md`: 面试官首先看到的公开项目首页。
- `docs/performance/fastmri_v1_eval.md`: 训练结果。
- `docs/performance/fastmri_v1_jetson_benchmark.md`: Jetson benchmark 汇总。
- `docs/assets/fastmri_v1_real/README.md`: 真实样例可视化。
- `ai_recon/scripts/train_fastmri_unet.py`: 正式训练脚本。
- `ai_recon/scripts/export_onnx.py`: ONNX 导出脚本。
- `ai_recon/scripts/make_recon_visualization.py`: 可视化脚本。
- `cpp_inference/src/tensorrt_backend.cpp`: C++ TensorRT backend。
- `firmware/README.md`: RTOS 控制侧下一阶段说明。

## 10. 面试时如何讲项目边界

需要诚实说明：

- 这个项目不是临床设备，也不做诊断。
- 当前 AI 和 Jetson 部署链路已经闭环。
- STM32/RTOS 控制侧目前是 scaffold，下一步会用 STM32F4 做 Zephyr pulse player。
- DICOM 链路是工程方向，当前 v1 benchmark 是 tensor-level reconstruction。
- fastMRI 数据和模型 artifact 不进 Git，仓库只保留脚本、文档、日志和小型可视化图片。

推荐总结：

> 这个项目的核心价值不是单点模型精度，而是把医学影像 AI 从训练、导出、边缘加速、C++ 服务接口到结果文档完整串起来。下一阶段我会把控制侧落到 STM32F4 + Zephyr，实现确定性 pulse sequence 播放和 Jetson 侧重建服务的串口协同。
