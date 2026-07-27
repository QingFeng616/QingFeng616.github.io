<!-- Docsify 放置建议：放到 docs/项目相关/ 目录下，文件名保持为 stm32-sound-event-project.md。
     在 _sidebar.md 的“项目相关”分组中添加：
     * [实时声音事件识别系统](项目相关/stm32-sound-event-project.md) -->

# 实时声音事件识别系统

> 基于 STM32F429 + FreeRTOS + LVGL 的端侧声音事件识别与可视化原型

## 项目简介

这是一个运行在 STM32F429I-DISC1 开发板上的**实时声音事件识别**系统。系统通过板载数字麦克风（I2S 接口）持续采集环境声音，在 MCU 上完成特征提取与事件判定，并将识别结果实时显示在板载 LCD 上（LVGL 图形界面）。整个系统基于 FreeRTOS 多任务调度，是一个典型的“感知—推理—显示”端侧嵌入式闭环。

项目目标不是追求 SOTA 识别精度，而是构建一个**完整、可演示、可扩展**的嵌入式 AI 原型，用于验证从音频采集、实时调度到图形交互的全链路工程能力。

## 技术栈

| 类别 | 选型 |
| --- | --- |
| MCU | STM32F429ZIT6（Cortex-M4，180 MHz，带 FMC/SDRAM、LTDC、DMA2D） |
| 开发框架 | STM32CubeMX + Keil MDK |
| RTOS | FreeRTOS（CMSIS_V2 封装） |
| GUI | LVGL v8.3 |
| 音频采集 | I2S2（数字麦克风，DMA 双缓冲） |
| 显示 | ILI9341（RGB 并口，LTDC 驱动）+ 板载 SDRAM 帧缓冲 |
| 存储（规划） | SPI1 接 microSD，存放模型 / 音频 |
| 触摸（规划） | 板载 STMPE811（I2C） |

## 系统架构

```
                I2S2 (PB12/13/PC3)
   数字麦克风 ──────────────┐
                            ▼
                   [ AudioCapture 任务 ]   FreeRTOS
                   I2S DMA 收数 → 特征/识别
                            │ 识别结果(event)
                            ▼
   LVGL 对象树 ──[ GUI 任务 ]──► draw buffer(SDRAM 0xD0110000)
                   lv_timer_handler          │ flush(脏矩形 memcpy)
                            │                ▼
                            │       帧缓冲 SDRAM 0xD0000000 (ARGB8888)
                            │                │ LTDC(DMA 扫描)
                            │                ▼
                            └────────► ILI9341 ──► LCD 显示
                                            ▲
                                     STMPE811(I2C, 规划中触摸)
```

- **帧缓冲与 LVGL 内存池**都放在板载 SDRAM（FMC Bank2，0xD0000000 起）。SDRAM 由 BSP 自带的 `BSP_SDRAM_Init()` 初始化。
- **LTDC** 以像素时钟持续扫描帧缓冲并输出到 ILI9341；改内存即改屏，无需 CPU 干预。
- **DMA2D** 预留用于图层混合 / 加速填充。

## 核心功能与亮点

- **端侧实时音频采集**：I2S + DMA 双缓冲，零拷贝送入处理任务，不阻塞其他任务。
- **多任务实时调度**：AudioCapture / Debug / GUI 三任务基于 FreeRTOS，职责清晰、栈与堆隔离。
- **图形化状态显示**：LVGL 在 320×240 LCD 上渲染识别状态，帧缓冲与 GUI 内存池均位于外部 SDRAM，缓解内部 SRAM 压力。
- **可扩展接口**：已预留 microSD（模型 / 录音）与触摸（STMPE811）硬件及软件接口。

## 工程难点与解决（最能体现能力的地方）

**1. 下载即崩溃 → FreeRTOS 堆不足**

- 现象：程序下载后跑不起来 / 直接 HardFault。
- 定位：FreeRTOS 全局堆 `configTOTAL_HEAP_SIZE` 仅 32 KB，三个任务的 TCB + 栈 + 队列都从这一池子扣，不够分配。
- 解决：在 **CubeMX（而非手写）** 把堆调到 64 KB，避免重新 Generate 被覆盖。同时厘清“堆不足”与“单任务栈溢出”的区别——后者要在 Tasks and Queues 单独调大该任务栈。

**2. 屏幕花屏 → 像素时钟 PLLSAI 配错**

- 现象：能亮但颜色错乱 / 撕裂。
- 根因：LTDC 像素时钟由 PLLSAI 提供，CubeMX 默认给成 25 MHz（应是 6 MHz）。
- 解决：CubeMX 中把 PLLSAI 配为 `192 / 4 / DIVR_8 = 6 MHz` 后重新 Generate，画面正常。

**3. 屏幕全黑 → SDRAM 被初始化了两次**

- 现象：GUI 任务运行但屏幕全黑。
- 根因：CubeMX 生成的 `MX_FMC_Init()` 初始化了一次 SDRAM，而 `BSP_Display_Init()` 内部的 `BSP_SDRAM_Init()` 又初始化了一次；两次 init 之间 BSP 已经访问过帧缓冲，第二次 `LOAD MODE REGISTER` 打乱了 SDRAM 状态，导致 LVGL 内存池（也在 SDRAM）不稳定。
- 解决（抗 Generate）：在 CubeMX 中**禁用 FMC 外设**，让 SDRAM 只由 BSP 初始化一次，彻底消除双 init，且重新 Generate 不会复发。

**4. LVGL 移植要点**

- `lv_conf.h` 关键三项：`LV_COLOR_DEPTH` 16→32（匹配 ARGB8888 帧缓冲）、`LV_MEM_ADR=0xD0100000`、`LV_MEM_SIZE=64KB`；draw buffer 置于 `0xD0110000`。
- flush 回调把 LVGL draw buffer 的脏矩形逐行 `memcpy` 到 `0xD0000000` 帧缓冲。

## 个人贡献

- 从 CubeMX 工程搭建、FreeRTOS 任务划分到 LVGL 移植与硬件 Bring-up 全流程独立完成。
- 主导三次关键故障的定位与根因分析（堆 / 像素时钟 / SDRAM 双 init），并形成可复用的排查方法。
- 设计了“CubeMX 管理外壳 + 自写实现文件”的代码组织方式，保证重新 Generate 不破坏手写逻辑。

## 成果与价值

- 在资源受限的 MCU 上跑通“采集—识别—显示”实时闭环，验证了端侧声音 AI 的可行性。
- 沉淀了一套 STM32 + FreeRTOS + LVGL + 外部 SDRAM 显示链路的 Bring-up 方法论，可直接复用于其他带屏嵌入式项目。

## 技能标签

`C` · `STM32` · `FreeRTOS` · `LVGL` · `I2S/DMA` · `FMC/SDRAM` · `LTDC/DMA2D` · `ILI9341` · `CubeMX` · `Keil MDK` · `嵌入式调试` · `硬件 Bring-up`
