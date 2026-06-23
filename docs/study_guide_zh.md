# 学习文档：如何吃透 MRI Edge RTOS AI 项目

这份文档不是项目说明书，而是你的学习路线。目标是让你能在面试中解释项目里的每个关键技术点，而不是只知道“脚本能跑”。

建议学习顺序：

```text
MRI/fastMRI 基础
  -> Python 数据处理和 FFT
  -> PyTorch U-Net 训练
  -> ONNX 导出
  -> TensorRT 和 Jetson 部署
  -> C++ 推理服务
  -> Zephyr RTOS 和 STM32 下一阶段
  -> 医疗软件工程意识
```

## 1. MRI 和 k-space 基础

你需要掌握：

- MRI 图像不是相机直接拍出来的，而是从频域数据 k-space 重建出来的。
- k-space 经过 inverse FFT 可以得到图像。
- 欠采样会减少采集时间，但会带来 aliasing 或结构伪影。
- zero-filled reconstruction 是最基础 baseline。

项目中对应文件：

- `ai_recon/src/mri_recon/zero_filled.py`
- `ai_recon/src/mri_recon/masks.py`
- `ai_recon/scripts/baseline_report.py`

你要能回答：

- 什么是 k-space？
- 为什么 undersampling 会让图像变差？
- zero-filled baseline 为什么有意义？
- 为什么 MRI 重建问题适合用深度学习做后处理？

推荐练习：

1. 打开 `zero_filled.py`，逐行看 `centered_fft2` 和 `centered_ifft2`。
2. 解释 `fftshift` 和 `ifftshift` 是为了把频谱中心移动到图像中心。
3. 用一句话说明 `zero_filled_magnitude(kspace)` 做了什么。

## 2. fastMRI HDF5 数据格式

你需要掌握：

- fastMRI 数据通常存储为 `.h5` 文件。
- 关键 dataset 是 `kspace`。
- single-coil 数据形状常见为 `(slices, height, width)`。
- 文件中可能有 `reconstruction_rss` 或 `reconstruction_esc` 作为 target。

项目中对应文件：

- `ai_recon/scripts/train_fastmri_unet.py`
- `ai_recon/scripts/make_recon_visualization.py`
- `docs/dataset.md`

你要能回答：

- 为什么训练脚本按 `(file_path, slice_index)` 建索引？
- 为什么不把全部 HDF5 一次性读进内存？
- train root 和 val root 为什么要分开？
- 为什么 smoke training 不能代表正式训练？

推荐练习：

```powershell
conda run -n base python -c "import h5py; f=h5py.File('your_file.h5','r'); print(list(f.keys())); print(f['kspace'].shape)"
```

## 3. 图像归一化和指标

你需要掌握：

- 模型训练前要把图像归一化到比较稳定的数值范围。
- L1 loss 衡量像素级误差。
- PSNR 是图像重建常用指标，越高表示越接近 target。
- 单张图的 PSNR 和整个验证集平均 PSNR可能不同。

项目中对应文件：

- `ai_recon/src/mri_recon/metrics.py`
- `ai_recon/scripts/train_fastmri_unet.py`
- `ai_recon/scripts/make_recon_visualization.py`

你要能回答：

- 为什么用 L1 loss？
- PSNR 怎么理解？
- 为什么真实可视化样例单 slice gain 只有 `+0.84 dB`，但验证集平均 gain 是 `+3.62 dB`？

参考回答：

> 单 slice 只是一个具体样本，受解剖结构、mask、噪声和模型泛化影响。项目最终指标看的是 1000 个 validation slices 的平均 PSNR，因此更稳定。

## 4. PyTorch U-Net

你需要掌握：

- U-Net 使用 encoder-decoder 和 skip connection。
- encoder 提取低分辨率语义特征。
- decoder 恢复空间分辨率。
- skip connection 保留细节。
- residual 输出可以让模型学习修正项。

项目中对应文件：

- `ai_recon/src/mri_recon/models.py`

你要能回答：

- 为什么用 U-Net？
- 为什么输出是 `x + self.out(d1)`？
- 这个模型和医学分割中的 U-Net 有什么相似和不同？

推荐练习：

1. 画出 `enc1 -> pool1 -> enc2 -> pool2 -> mid -> up2 -> dec2 -> up1 -> dec1 -> out`。
2. 标出每个阶段 channel 数：`1 -> 16 -> 32 -> 64 -> 32 -> 16 -> 1`。
3. 解释 `torch.cat([d2, e2], dim=1)` 为什么 channel 会相加。

## 5. 正式训练脚本

重点文件：

- `ai_recon/scripts/train_fastmri_unet.py`

你需要看懂这些函数或类：

- `FastMriSliceDataset`
- `_undersample`
- `_center_crop`
- `_normalize`
- `make_loader`
- `evaluate`
- `checkpoint_payload`
- `write_report`
- `main`

你要能回答：

- 训练脚本如何构造样本？
- 为什么要保存 best 和 last 两个 checkpoint？
- `--resume` 有什么用？
- `--amp` 为什么能加速？
- 为什么要写 `docs/performance/fastmri_v1_eval.md`？

推荐讲法：

> 训练脚本不是简单调用框架，而是完整处理了 HDF5 indexing、动态欠采样、zero-filled 输入、target 读取、center crop、归一化、AMP、checkpoint、resume 和报告写出。

## 6. ONNX 导出

重点文件：

- `ai_recon/scripts/export_onnx.py`

你需要掌握：

- ONNX 是模型中间表示，用于跨框架部署。
- PyTorch checkpoint 不能直接给 TensorRT 用。
- ONNX 导出需要 dummy input。
- 输入名 `masked_image` 会在 TensorRT 构建时使用。

你要能回答：

- 为什么要从 `.pth` 导出 `.onnx`？
- dummy input 的 shape 为什么是 `1x1x320x320`？
- 为什么脚本要读取 checkpoint 中的 `crop_size`？
- Windows 为什么会遇到 `PosixPath` 问题？

推荐回答：

> `.pth` 是 PyTorch 自己的权重格式，TensorRT 不能直接加载。ONNX 是中间交换格式。导出时用 dummy input trace 出计算图，并固定输入 shape，便于 TensorRT 做静态优化。

## 7. TensorRT 和 Jetson

你需要掌握：

- TensorRT 会把 ONNX 图优化成设备相关的 engine。
- FP16 可以降低计算和内存压力。
- engine 和具体设备、TensorRT 版本、shape 有关，不适合直接提交到 Git。
- `trtexec` 是验证 ONNX 可部署性的标准工具。

项目中对应文件：

- `docs/performance/trtexec_fastmri_v1_fp16.log`
- `docs/performance/fastmri_v1_jetson_benchmark.md`

你要能回答：

- ONNX 和 TensorRT engine 的区别是什么？
- `--fp16` 做了什么？
- `--shapes=masked_image:1x1x320x320` 为什么必须和导出输入名一致？
- `trtexec` latency 和 C++ latency 为什么不同？

推荐回答：

> ONNX 是平台无关模型图，TensorRT engine 是在 Jetson 上针对具体 GPU、精度和 shape 优化后的执行计划。`trtexec` 证明模型能被 TensorRT 解析和加速，C++ smoke 则证明项目自己的服务代码能加载和运行 engine。

## 8. C++ TensorRT 推理服务

重点文件：

- `cpp_inference/include/mri/inference_engine.hpp`
- `cpp_inference/src/tensorrt_backend.cpp`
- `cpp_inference/src/main.cpp`

你需要掌握：

- C++ 服务层的作用是隔离模型推理实现。
- TensorRT runtime 需要反序列化 engine。
- CUDA buffer 分 host 和 device。
- 推理前要绑定 input/output tensor address。
- `enqueueV3` 是实际执行推理的入口。

你要能回答：

- 为什么需要 C++ 服务，而不是只用 Python？
- RAII 在这个 C++ 代码中有什么用？
- 为什么要记录 `latency_ms_mean/min/max`？
- 输出 `102400 elements` 表示什么？

推荐回答：

> 真实嵌入式或边缘部署场景通常需要 C++ 服务接口，因为它更容易和系统服务、设备 IO、实时控制链路集成。Python 训练负责模型开发，C++ 推理负责部署边界。

## 9. 可视化脚本

重点文件：

- `ai_recon/scripts/make_recon_visualization.py`
- `docs/assets/fastmri_v1_real/README.md`

你需要掌握：

- 可视化不是训练的一部分，而是结果解释的一部分。
- contact sheet 的四列分别是什么。
- 单样本 PSNR 只能作为例子，不代表整体指标。
- 脚本支持真实 HDF5，也支持 phantom fallback。

你要能回答：

- 为什么需要可视化？
- 输入 k-space 图为什么看起来不像 MRI 图像？
- zero-filled 和 target 的差异是什么？
- model reconstruction 改善了什么？

推荐回答：

> 指标能说明平均效果，但可视化能让面试官直观看到链路是否真实。这个脚本把同一个 slice 的欠采样输入、baseline、模型输出和目标图放在一起，方便解释模型做了什么。

## 10. 本地环境问题和修复方式

这次遇到的问题：

- `h5py` DLL 报错。
- `Pillow/Matplotlib` DLL 报错。
- 原因是 Anaconda base 环境里 pip 版 `h5py 3.1.0` 和 conda 的 HDF5 依赖混装。

修复后的状态：

- `h5py 3.7.0`
- `hdf5 1.10.6`
- `matplotlib 3.6.2`

推荐运行方式：

```powershell
conda run -n base python ai_recon/scripts/make_recon_visualization.py --help
```

你要能回答：

- 为什么 Python 包会有 DLL 问题？
- 为什么 conda 和 pip 混装科学计算包容易出问题？

推荐回答：

> 像 h5py、Pillow 这种包依赖 C/C++ 动态库。Windows 下如果包来自 pip，而底层 HDF5/JPEG/PNG DLL 来自 conda，版本或搜索路径不匹配就会导入失败。解决方式是让二进制依赖来自同一个包管理体系，并通过 conda 激活环境。

## 11. RTOS/STM32 下一阶段需要学什么

虽然当前阶段先整理文档，但下一步会进入 STM32F4 + Zephyr。

你需要提前补：

- Zephyr project structure。
- devicetree 和 board config。
- GPIO、timer、UART API。
- thread priority 和 workqueue。
- timing jitter 测量。
- 简单串口协议设计。

项目中对应文件：

- `firmware/README.md`
- `firmware/sequences/spin_echo_demo.json`
- `tools/validate_sequence.py`

下一阶段目标：

1. 把 Zephyr 工程适配到你的 STM32F4 board。
2. 播放一个 JSON pulse sequence。
3. 用 GPIO 或 UART 输出事件。
4. 测量 tick jitter 或事件间隔。
5. 和 Jetson 侧重建服务形成控制消息闭环。

## 12. 面试前复习清单

你应该能不用看文档回答：

- 这个项目整体架构是什么？
- fastMRI 数据怎么进模型？
- zero-filled baseline 是什么？
- U-Net 输入输出是什么？
- 训练脚本保存了哪些产物？
- ONNX 导出为什么需要 dummy input？
- TensorRT engine 是怎么构建的？
- C++ backend 如何加载和执行 engine？
- 项目真实测得的 PSNR 和 latency 是多少？
- 当前项目边界和下一步计划是什么？

建议最后背熟的数字：

- Train slices: `10000`
- Validation slices: `1000`
- Acceleration: `4x`
- Crop size: `320x320`
- Best validation PSNR: `26.49 dB`
- Zero-filled validation PSNR: `22.87 dB`
- PSNR gain: `+3.62 dB`
- TensorRT host latency mean: `5.65 ms`
- C++ smoke latency mean: `8.30 ms`
