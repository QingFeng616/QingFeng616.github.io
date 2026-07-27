<!-- Docsify 放置建议：放到 docs/开发日记/ 目录下，文件名保持为 sound-event-dev-diary.md。
     在 _sidebar.md 的“开发日记”分组中添加：
     * [声音事件识别系统·开发日记](开发日记/sound-event-dev-diary.md) -->

# 声音事件识别系统 · 开发日记

> 记录从工程零搭建到 LCD 出图的完整过程。偏流水账，供复盘与面试复盘用。

## 2026-07-22 环境搭建与硬件对齐

- 用 CubeMX 建工程：STM32F429I-DISC1，HSE 设为 BYPASS（板载 ST-LINK 提供 8 MHz MCO），否则时钟起不来直接卡死。
- 开外设：FMC（SDRAM）、LTDC、DMA2D、SPI5（LCD 命令）、I2S2（麦克风）、SPI1（microSD）、USART1（调试）。
- 确认关键引脚：I2S2 的 CK=PB13 / WS=PB12 / SD=PC3；ILI9341 命令 SPI5（PF7 SCK / PF9 MOSI），CS=PC2 / DC=PD13 / RST=PD12；SDRAM Bank2 映射 `0xD0000000`。
- 引入 FreeRTOS（CMSIS_V2），先建 AudioCapture / Debug 两个任务。

## 2026-07-24 任务划分与 ST BSP 接入

- 把 ST 官方 BSP 平铺进 `BSP/`：`discovery_sdram.c/.h`、`discovery_lcd.c/.h`、`Components/ili9341/`、`Utilities/Fonts/`、`Common/lcd.h`。
- 修 include 依赖：`discovery_lcd.h` 去掉对 `stm32f429i_discovery.h` 的引用，字体路径改 `Fonts/...`。
- 发现字体坑：`discovery_lcd.c` 里 `#include "Fonts/font*.c"` 已编字模，Keil 里要把 `BSP/Fonts` 组里 5 个 `font*.c` 从编译中 Remove（不删盘）。
- 自写 `bsp_display.c`：实现 `LCD_IO_*` 胶水（用 CubeMX 的 `hspi5` + 自 init PC2/PD13/PD12），`BSP_Display_Init()` 串起 LCD 初始化与清屏。

## 2026-07-25 LVGL 移植与图层

- 引入 LVGL v8.3 源码，`lv_conf.h` 三改：`#if 0→#if 1`、`LV_COLOR_DEPTH 16→32`、`LV_MEM_SIZE` 设 64KB 且 `LV_MEM_ADR=0xD0100000`；draw buffer 在 `0xD0110000`。
- `lv_port_disp.c`：flush 回调把 draw buffer 脏矩形逐行 `memcpy` 到 `0xD0000000` 帧缓冲。
- Keil 加文件：LVGL 的 185 个 `src/*.c` + `porting/lv_port_disp.c` + `tasks/gui_task.c`；IncludePath 加 LVGL 根与 porting；Define 必须加 `LV_CONF_INCLUDE_SIMPLE`（armcc 无 `__has_include`，否则 180 个 `cannot open ../../lv_conf.h`）。
- 建 GUI 任务，写 `gui_task_main()`：`lv_init` → `lv_port_disp_init` → 建 "LVGL OK" 标签 → `for(;;)` 里 `lv_tick_inc` + `lv_timer_handler` + `osDelay(5)`。

## 2026-07-26 花屏修复（PLLSAI）

- 现象：屏能亮但花屏。
- 根因：LTDC 像素时钟 PLLSAI 被 CubeMX 配成 25 MHz（应 6 MHz）。
- 修法：CubeMX 改 PLLSAI = `192 / 4 / DIVR_8 = 6 MHz`，重新 Generate。已验证点亮。

## 2026-07-27 堆不足 + SDRAM 双 init

- 现象：三任务一起建，下载即崩。
- 定位：FreeRTOS 全局堆 `configTOTAL_HEAP_SIZE` 仅 32 KB 不够分。
- 解决：在 **CubeMX** 把堆调到 64 KB（不能手改 `FreeRTOSConfig.h`，会被 Generate 覆盖）；GuiTask 栈 8192 B。
- 同时把 GUI 任务改为 CubeMX 原生管理（Tasks and Queues 加 GuiTask，Entry `StartGuiTask`），源码重构：`StartGuiTask` 外壳调 `gui_task_main`，删掉 `guiTask_attr`。
- 残留隐患：发现 `MX_FMC_Init()` 仍在 `main.c`，与 `BSP_SDRAM_Init` 形成 SDRAM 双 init（之前全黑根因）。下一步在 CubeMX 禁用 FMC 外设，让 SDRAM 只 init 一次，且抗 Generate。

## 待办 / 下一步

- [ ] CubeMX 禁用 FMC，Generate 验证 `main.c` 不再有 `MX_FMC_Init`。
- [ ] Keil Rebuild + Download，确认屏显 `LVGL OK`。
- [ ] 移植 STMPE811 触摸（复制 `stm32f429i_discovery_ts.c/.h` + CubeMX 开 I2C），做 LVGL indev port。
- [ ] 把测试标签换成真实的声音事件状态界面（识别结果、置信度等）。
- [ ] （规划）microSD 载入模型 / 录音，AudioCapture 任务接入真实识别算法。
