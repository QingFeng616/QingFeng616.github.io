<!-- Docsify 放置建议：放到 docs/博客文章/ 目录下，文件名保持为 stm32f429-lvgl-bringup.md。
     在 _sidebar.md 的“博客文章”分组中添加：
     * [在 STM32F429 上点亮 LVGL：从黑屏到显示的 Bring-up 实战](博客文章/stm32f429-lvgl-bringup.md) -->

# 在 STM32F429 上点亮 LVGL：从黑屏到显示的 Bring-up 实战

> 一块带 SDRAM 和 RGB 屏的 MCU，把图形库跑起来到底要过哪几关？记录一次完整的嵌入式 GUI Bring-up。

## 引言

在 MCU 上做图形界面，很多人以为“把 LVGL 移植进去、调个 `lv_label_set_text` 就行”。真上手才知道，屏幕背后是一条由 **SDRAM、FMC、LTDC、PLLSAI、FreeRTOS 堆** 串起来的链路，任何一环配错，轻则花屏、重则全黑，连报错都没有。

本文以 STM32F429I-DISC1 + ILI9341（RGB 屏）+ LVGL v8.3 为例，复盘我从“工程建好”到屏幕上出现 `LVGL OK` 这行字，所闯过的三关。希望能帮你在自己的带屏项目里少走弯路。

<!-- more -->

## 硬件与软件底座

- MCU：STM32F429ZIT6，外挂 16MB SDRAM（FMC Bank2，映射在 `0xD0000000`）。
- 屏幕：ILI9341，命令走 SPI5，像素走 LTDC 的 RGB 并口；帧缓冲放在 SDRAM，图层格式 ARGB8888。
- 软件：CubeMX 生成 HAL + FreeRTOS（CMSIS_V2），Keil 编译，LVGL 作为中间件引入。

先建立一个关键认知：**LCD 本身只是个“执行器”**。CPU 通过 FMC 把像素写进 SDRAM 里的帧缓冲，LTDC 这个硬件模块再按像素时钟用 DMA 把帧缓冲扫到屏幕上。所谓“GUI 库”，本质是在帧缓冲上画像素，并把“哪块区域脏了”告诉 LTDC。理解了这条数据流，后面三个坑就都能解释了。

## 第一关：花屏——像素时钟 PLLSAI 配错

工程第一次编译下载，屏幕“亮了”，但颜色完全错乱、像被撕裂。

根因很快定位到 **LTDC 的像素时钟来源 PLLSAI**。CubeMX 默认给我配成了 25 MHz，而这块屏的 RGB 时序需要的是 6 MHz。时钟不对，LTDC 扫行的节拍就错，于是花屏。

修法在 CubeMX：把 PLLSAI 配成 `192 / 4 / DIVR_8 = 6 MHz`，重新 Generate。这里有个坑：**你之前在代码里手动改的时钟，重新 Generate 会被覆盖**，所以必须改在 CubeMX 里。

> 教训：带屏项目的第一个时钟一定是像素时钟，先把它和屏手册对上，再谈别的。

## 第二关：全黑——SDRAM 被初始化了两次

花屏修好后，我进一步把 LVGL 移植进来。GUI 任务明明在跑（调试口能看到 `lv_timer_handler` 在循环），屏幕却**全黑**。

这是最隐蔽的一关。链路是这样的：

1. CubeMX 生成了 `MX_FMC_Init()`，它在 `main()` 里先把 SDRAM 初始化了一次（FMC 控制器 + 时序 + 模式寄存器）。
2. 我的显示初始化 `BSP_Display_Init()` 内部会调用 ST 的 `BSP_LCD_Init()`，而它又调用 `BSP_SDRAM_Init()`——**第二次**初始化 SDRAM。
3. 关键在两次 init 之间：BSP 已经访问过帧缓冲（配图层、清屏），也就是 SDRAM 已经被写过；第二次 init 末尾的 `LOAD MODE REGISTER` 命令，会把已经用起来的 SDRAM 状态打乱。
4. LVGL 的内存池也在 SDRAM（`0xD0100000`）。内存池一旦不稳定，GUI 画出来的东西就全丢——于是全黑。

为什么不能直接注释掉 `MX_FMC_Init()`？因为那是 CubeMX 生成的代码，**重新 Generate 又会回来**。正确且抗 Generate 的做法是：在 CubeMX 里直接**禁用 FMC 外设**。BSP 的 `BSP_SDRAM_Init()` 是自包含的（自带 FMC 时钟使能、GPIO 配置、时序），禁用 CubeMX 的 FMC 后，SDRAM 只被初始化一次，且以后 Generate 不会再插入 `MX_FMC_Init`。

> 教训：SDRAM 初始化命令序列（PRECHARGE / REFRESH / LOAD MODE REGISTER）只能跑一次，且要在任何访问之前。混用 CubeMX-FMC 和 BSP-SDRAM 两套初始化是经典雷区。

## 第三关：下载即崩——FreeRTOS 堆不够

屏幕问题解决后，我把 AudioCapture、Debug、GUI 三个任务都建起来，一下载就崩。

原因在 FreeRTOS 的**全局堆** `configTOTAL_HEAP_SIZE`。所有任务的 TCB、栈、队列、信号量都从这一池子里分配。我之前只有 32 KB，三个任务的栈加起来就不够分，创建任务失败 → 系统起不来。

注意区分两个概念，很多人会搞混：

- **堆不足**：`configTOTAL_HEAP_SIZE` 太小 → 调大这个宏（同样要在 CubeMX 里改，否则 Generate 覆盖）。
- **单任务栈溢出**：某个任务自己栈不够 → 在 CubeMX 的 Tasks and Queues 里单独调大那个任务的 Stack Size，加堆没用。

我把全局堆调到 64 KB，GUI 任务栈设为 8192 字节，问题消失。

## 收尾：看到 “LVGL OK”

三关过后，屏幕终于稳定显示一行 `LVGL OK`。此时的数据流是完整的：

```
LVGL 对象树 → draw buffer(SDRAM 0xD0110000) → flush memcpy → 帧缓冲(0xD0000000)
            → LTDC(DMA 扫描) → ILI9341 → LCD
```

顺带一提代码组织：我把“任务外壳”交给 CubeMX 生成（`StartGuiTask` 由 MX 注册），真正的实现写在自己的 `gui_task.c` 里（`gui_task_main`）。这样重新 Generate 永远不会覆盖我的业务逻辑——这是带 CubeMX 的项目必须养成的习惯。

## 复盘：嵌入式 GUI 上手的几个坑

1. **先对时钟，再谈显示**：像素时钟（PLLSAI）不对 = 花屏。
2. **SDRAM 只 init 一次**：别让 CubeMX-FMC 和 BSP-SDRAM 叠加。
3. **堆 / 栈分开看**：FreeRTOS 崩，先想是全局堆不够还是某任务栈溢出。
4. **改配置进 CubeMX**：凡是 Generate 会覆盖的地方，改动都要回到 CubeMX，别在生成代码里手改。
5. **理解数据流**：屏只是执行器，CPU 写帧缓冲、LTDC 扫帧缓冲、GUI 库算像素——搞清这条线，所有显示问题都有迹可循。

## 结语

把 LVGL 在 STM32 上点亮，真正的难点从来不在 LVGL 本身，而在它背后那串硬件链路。趟过这三关之后，再往屏上加按钮、图表、触摸，就只是“在帧缓冲上画画”的事了。
