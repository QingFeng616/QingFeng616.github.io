<!-- Docsify 放置建议：放到 docs/博客文章/ 目录下，文件名保持为 stm32f429-lvgl-bringup.md。
     在 _sidebar.md 的“博客文章”分组中添加：
     * [在 STM32F429 上点亮 LVGL：MCU 图形界面从零到显示](博客文章/stm32f429-lvgl-bringup.md) -->

# 在 STM32F429 上点亮 LVGL：MCU 图形界面从零到显示

> 当一块几十块钱的 Cortex-M4 开发板也能跑出流畅的图形界面，嵌入式产品的交互门槛就被彻底拉低了。本文记录把 LVGL 移植到 STM32F429 + 外部 SDRAM + RGB 屏的完整过程，并讲清背后那条显示链路。

## 引言：为什么要在 MCU 上做 GUI

过去，"带屏幕的嵌入式设备"要么用段码 LCD，要么外挂一颗昂贵的显示控制器。今天，随着 STM32F4/F7/H7 这类带 LTDC（LCD-TFT 控制器）和外部 SDRAM 的 MCU 普及，在一颗 MCU 上直接驱动彩色屏、跑图形库已经成为常态：

- 家电面板、工控 HMI、医疗仪器、充电桩、IoT 网关配置页……
- 用户期待的是"像手机一样"的体验：按钮、滑动、动画、图表。

但 MCU 不是手机 SoC：没有 GPU、内存以 KB/MB 计、还要和实时控制任务抢资源。所以"在 MCU 上做 GUI"本质是**在极受限资源下，把一帧帧像素准时搬到屏幕上**。本文以 STM32F429I-DISC1 开发板（板载 ILI9341 RGB 屏 + 16MB SDRAM）为例，用 LVGL 把这件事跑通，并拆开它背后的每一层。

## LVGL 是什么，它到底怎么工作

LVGL（Light and Versatile Graphics Library）是目前最流行的开源嵌入式 GUI 库（MIT 协议），特点是**与硬件无关、资源占用小、控件丰富**。它本身不碰任何寄存器，只做一件事：**在内存里算出每个像素该是什么颜色，再通过一个回调把结果交给你**。

它的内部运转可以拆成四步：

1. **对象树（Object Tree）**：你用 `lv_label_create()`、`lv_btn_create()` 等 API 建的每一个控件，都挂在屏幕（screen）之下。LVGL 维护这棵树。
2. **脏区域（Dirty Area）**：当某个控件内容变化（比如改了文字），LVGL 只把它影响的矩形标记为"脏"，而不是整屏重画——这是它省算力的关键。
3. **绘制引擎（Draw Engine）**：在每次"心跳"里，LVGL 遍历脏区域，在**绘制缓冲（draw buffer）**里算出这些像素的颜色值。
4. **Flush 回调（你来实现）**：算完后 LVGL 调用你注册的 `flush` 回调，把你画好的那块脏矩形**拷贝到你指定的帧缓冲地址**。真正把像素送上屏的动作，由硬件（见下节）完成。

> 还有一个容易被忽视的点：**LVGL 不是线程安全的**。它靠一个"心跳"驱动——你要周期性调用 `lv_timer_handler()`（通常放在一个独立任务/定时器里），并用 `lv_tick_inc()` 告诉它"过去了多少毫秒"。屏幕刷新、动画、输入处理全靠这个心跳推进。

一句话总结数据流：**对象树变化 → 标脏 → 在 draw buffer 算像素 → flush 搬进帧缓冲 → 硬件把帧缓冲扫到屏**。理解了这条线，后面所有问题都有迹可循。

## 硬件底座：STM32F429 的显示链路

STM32F429 之所以能直接带彩屏，靠的是三块硬件协同：

```
        CPU (Cortex-M4)
          │ 通过 FMC 写像素
          ▼
   ┌──────────────┐
   │ 外部 SDRAM    │  ← 帧缓冲 + LVGL 内存池 (0xD0000000 起, 16MB)
   └──────────────┘
          │ LTDC 按像素时钟用 DMA 读取
          ▼
   ┌──────────────┐
   │ LTDC 控制器   │  ← 生成 HSYNC/VSYNC/DE + 像素时钟(PLLSAI)
   └──────────────┘
          │ RGB 并口
          ▼
      ILI9341 屏  ← 只是个"执行器"：按时序把 RGB 数据锁存到面板
```

- **FMC（Flexible Memory Controller）**：把外部 SDRAM 映射成一片地址空间（Bank2 在 `0xD0000000`）。CPU 像访问内存一样往里写像素；LVGL 的帧缓冲和内存池都放在这里。
- **LTDC**：一个带 DMA 的显示控制器。你给它"帧缓冲地址 + 时序参数"，它就**自顾自地**按像素时钟把帧缓冲一行行扫出来，完全不占 CPU。所谓"改内存即改屏"，就是因为 LTDC 一直在扫这块内存。
- **PLLSAI**：专门给 LTDC 提供像素时钟。时钟频率必须和屏的 RGB 时序匹配，否则花屏。
- **ILI9341**：屏驱芯片，只负责按时序把 RGB 数据锁存显示——它不参与任何图形计算。

> 关键认知：**LCD 只是执行器**。真正"画"的是 LVGL（在 SDRAM 里算像素），真正"搬"的是 LTDC（DMA 扫 SDRAM）。CPU 在这条链路上只负责"写 SDRAM"，可以腾出手做别的实时任务。

## 移植实战：从零到出图

下面是用 CubeMX + Keil + LVGL v8.3 落地的实际步骤。

### 1. 工程与外设规划（CubeMX）

开这些外设：FMC（接 SDRAM）、LTDC（RGB 屏）、DMA2D（图层混合/加速，可选先用）、SPI5（给 ILI9341 发命令）、I2S2（麦克风，本项目还要采音）、USART1（调试打印）。STM32F429I-DISC1 的 HSE 要设成 **BYPASS**（板载 ST-LINK 通过 MCO 提供 8MHz），否则时钟起不来直接卡死。

### 2. lv_conf.h 关键配置

LVGL 的行为几乎都由一个 `lv_conf.h` 决定。本项目最关键的几项：

```c
#define LV_COLOR_DEPTH 32          // 匹配 ARGB8888 帧缓冲（默认 16 不对）
#define LV_MEM_SIZE (64 * 1024)    // LVGL 内部内存池 64KB
#define LV_MEM_ADR 0xD0100000      // 内存池放在 SDRAM（避开帧缓冲区）
#define LV_TICK_CUSTOM 0           // 关闭 LVGL 自带 tick，改用手动 lv_tick_inc
```

**代码清单**：这段配置给了 3 个东西——① `LV_COLOR_DEPTH 32`：告诉 LVGL 每个像素用 32 位（对应帧缓冲的 ARGB8888 格式，否则颜色错位）；② `LV_MEM_ADR / LV_MEM_SIZE`：把 LVGL 自己用的内存池放到外部 SDRAM 的 `0xD0100000`（帧缓冲在 `0xD0000000`，两者隔开避免踩踏）；③ `LV_TICK_CUSTOM 0`：关掉库自带的时间源，改用我们在任务里手动喂时钟（见第 4 步）。

### 3. 显示端口 lv_port_disp：flush 回调

LVGL 算完像素后，要由我们把脏矩形搬进帧缓冲。核心就是一个 `memcpy`：

```c
void disp_flush(lv_disp_drv_t * drv, const lv_area_t * area, lv_color_t * color_p)
{
    int32_t w = area->x2 - area->x1 + 1;
    for (int32_t y = area->y1; y <= area->y2; y++) {
        lv_color_t *dst = (lv_color_t *)FRAME_BUFFER + y * LV_HOR_RES + area->x1;
        lv_color_t *src = color_p + (y - area->y1) * w;
        memcpy(dst, src, w * sizeof(lv_color_t));   // 逐行拷脏矩形
    }
    lv_disp_flush_ready(drv);   // 必须调用：告诉 LVGL 这帧搬完了
}
```

**代码清单**：`disp_flush` 是 LVGL 显示端口唯一需要你实现的"搬运工"。它做两件事——① 遍历脏矩形 `area` 的每一行，把 draw buffer 里的像素 `memcpy` 到 SDRAM 帧缓冲 `FRAME_BUFFER` 的对应位置（逐行是因为帧缓冲是连续的一维数组，行首地址 = `y * 屏宽`）；② 调用 `lv_disp_flush_ready()` 通知 LVGL 本帧已送达，否则 LVGL 会一直等、界面卡死。

### 4. GUI 任务与心跳（FreeRTOS）

LVGL 要"心跳"才能动。放在一个独立 FreeRTOS 任务里最干净：

```c
void gui_task_main(void *argument)
{
    (void)argument;
    lv_init();
    lv_port_disp_init();                       // 注册 flush 等显示端口

    lv_obj_t *label = lv_label_create(lv_scr_act());
    lv_label_set_text(label, "LVGL OK");
    lv_obj_align(label, LV_ALIGN_CENTER, 0, 0);

    uint32_t last = osKernelGetTickCount();
    for (;;) {
        uint32_t now = osKernelGetTickCount();
        lv_tick_inc(now - last);               // 喂毫秒时钟
        last = now;
        lv_timer_handler();                    // 心跳：重绘脏区/动画/输入
        osDelay(5);                            // 让出 CPU 给其它任务
    }
}
```

**代码清单**：`gui_task_main` 是 GUI 任务的"发动机"。流程——① `lv_init()` + `lv_port_disp_init()` 初始化库和显示端口；② 建一个居中标签 "LVGL OK" 作最小验证；③ `for(;;)` 里三件事：`lv_tick_inc()` 用 RTOS 滴答算出流逝毫秒喂给 LVGL、`lv_timer_handler()` 推进心跳（真正重绘发生在这里）、`osDelay(5)` 把 CPU 让给 AudioCapture 等其它任务。这就是 LVGL "非线程安全、靠单心跳驱动" 的工程落地。

### 5. 让 CubeMX 与手写代码和平共处

CubeMX 的 Generate Code 会覆盖它生成的文件。我的做法是：**任务"外壳"交给 MX 生成**（`StartGuiTask` 由 MX 在 Tasks and Queues 里注册），**真正的实现写在自己的 `gui_task.c`**（`gui_task_main`）。MX 生成的 `StartGuiTask` 函数体只写一行 `gui_task_main(argument);`。这样重新 Generate 永远不会覆盖业务逻辑——这是带 CubeMX 的项目必须养成的习惯。

## 资源账本：这块屏吃掉多少内存

很多人担心"GUI 会不会把 MCU 内存吃光"。算笔账就清楚了（以 320×240 屏为例）：

- **帧缓冲**：ARGB8888 = 4 字节/像素 → `320 × 240 × 4 ≈ 300 KB`。
- **LVGL 内存池**：64 KB（控件对象、临时缓冲）。
- **draw buffer**：可只开局部（如 320×40 ≈ 50 KB），不必全屏。

合计约 **400 KB+**，而 STM32F429 内部 SRAM 总共才 ~256 KB——**单帧缓冲就放不下**，所以必须靠外部 SDRAM（本项目 16 MB，绰绰有余）。这正是 FMC + SDRAM 在这类带屏项目里不可或缺的原因。

## 三个真实踩坑：原理没对齐就会踩

下面三个坑，本质都是"某一层原理没和硬件对齐"。它们不是孤立的 bug，而是前面那张链图的反面教材。

**坑一：花屏 = 像素时钟 PLLSAI 不对**
CubeMX 默认把 LTDC 的像素时钟（来自 PLLSAI）配成 25 MHz，而屏需要 6 MHz。时钟不对，LTDC 扫行节拍错 → 花屏。修法：CubeMX 里把 PLLSAI 配成 `192 / 4 / DIVR_8 = 6 MHz` 后重新 Generate。**凡是 Generate 会覆盖的配置，改动都要回到 CubeMX。**

**坑二：全黑 = SDRAM 被初始化两次**
CubeMX 生成的 `MX_FMC_Init()` 初始化了一次 SDRAM，而 `BSP_Display_Init()` 内部的 `BSP_SDRAM_Init()` 又初始化了一次；两次之间 BSP 已访问过帧缓冲，第二次 init 的 `LOAD MODE REGISTER` 打乱了 SDRAM 状态，LVGL 内存池（也在 SDRAM）随即不稳 → 全黑。修法（抗 Generate）：**在 CubeMX 里禁用 FMC 外设**，让 SDRAM 只由 BSP 初始化一次。

**坑三：下载即崩 = FreeRTOS 堆不够**
三个任务一起建就崩。根因是 FreeRTOS 全局堆 `configTOTAL_HEAP_SIZE` 只有 32 KB，所有 TCB/栈/队列都从这一池扣，不够分。调大到 64 KB 解决。注意区分：某任务**自己**栈溢出要单独调大该任务栈，加全局堆没用。

## 可复用的 Bring-up 检查清单

把上面的经验压成一份清单，换任何带屏 MCU 都能用：

1. 先对**像素时钟**（PLLSAI / 屏手册时序），再谈显示。
2. SDRAM / 显存只在**一处**初始化，且要在任何访问之前。
3. FreeRTOS 崩：先想是**全局堆**不够，还是某任务**栈溢出**。
4. 帧缓冲 / LVGL 内存池地址**错开**，且确认落在可用 RAM（不够就上外部 SDRAM）。
5. `flush` 回调末尾**必须** `lv_disp_flush_ready()`，否则界面卡死。
6. LVGL 心跳（`lv_tick_inc` + `lv_timer_handler`）必须按时跑，且**不要多线程并发调 LVGL API**。
7. 凡是 Generate 会覆盖的配置，改动回到 CubeMX。

## 延伸：接下来能做什么

点亮只是起点。基于这套底座可以接着做：

- **触摸**：板载 STMPE811（I2C）接上 LVGL 的 indev 端口，界面就能点。
- **图表与控件**：用 LVGL 的 chart / slider / list 做数据可视化面板。
- **真实应用**：把 AudioCapture 任务采到的声音做成"声音事件识别"状态界面——本项目的最终目标。

## 结语

在 STM32 上把 LVGL 点亮，真正的难点从不在 LVGL 本身，而在它背后那条"CPU 写 SDRAM → LTDC 扫 SDRAM → ILI9341 显示"的链路。把每一层的原理和硬件对齐，三个坑其实都可以提前避开。趟过这一遍，再往屏上加按钮、图表、触摸，就只是"在帧缓冲上画画"的事了。
