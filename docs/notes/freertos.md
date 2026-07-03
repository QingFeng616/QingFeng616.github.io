# FreeRTOS 学习

> 持续更新中...

---

## 简介

FreeRTOS 是一个开源的实时操作系统（RTOS），广泛应用于嵌入式系统。

## 核心概念

| 概念 | 说明 |
|------|------|
| Task（任务） | 独立执行的线程 |
| Queue（队列） | 任务间通信机制 |
| Semaphore（信号量） | 资源同步与互斥 |
| Timer（定时器） | 软件定时器 |

## 常用 API

```c
// 创建任务
xTaskCreate(vTaskFunction, "Name", StackSize, NULL, Priority, &Handle);

// 启动调度器
vTaskStartScheduler();

// 延时
vTaskDelay(pdMS_TO_TICKS(100));
```
## 移植FreeRTOS后的delay函数重写

### 一、取消注释

先取消"#include "stm32f10x_it.h""与"FreeRTOSConfig.h"当中关于下面宏的注释：
```c
#define xPortSysTickHandler SysTick_Handler
```
### 二、添加宏

在"FreeRTOSConfig.h"添加下面的宏：
```c
#define INCLUDE_xTaskGetSchedulerState 1
```
### 三、重构Delay函数

delay.c
```c
#include "delay.h"
 
static uint16_t fac_ms = 8;  // 用于存储每毫秒的 SysTick 计数
static uint32_t fac_us;      // 用于存储每微秒的 SysTick 计数
 
// SysTick 中断服务函数，用于 FreeRTOS 的时钟节拍
extern void xPortSysTickHandler(void);
void SysTick_Handler(void)
{
    // 如果 FreeRTOS 调度器已经启动，则调用 FreeRTOS 的 SysTick 处理函数
    if (xTaskGetSchedulerState() != taskSCHEDULER_NOT_STARTED)
    {
        xPortSysTickHandler();
    }
}
 
// 初始化延时函数
// 当使用操作系统时，此函数会初始化操作系统的时钟节拍
// SysTick 的时钟固定为 HCLK 时钟的 1/8
void delay_init(void)
{
#if SYSTEM_SUPPORT_OS  // 如果需要支持操作系统
    u32 reload;
#endif
 
    // 配置 SysTick 时钟源为 HCLK（系统时钟）
    SysTick_CLKSourceConfig(SysTick_CLKSource_HCLK);
    fac_us = SystemCoreClock / 1000000;  // 计算每微秒的 SysTick 计数
 
#if SYSTEM_SUPPORT_OS  // 如果需要支持操作系统
    // 计算 SysTick 重装载值，用于 FreeRTOS 的时钟节拍
    reload = SystemCoreClock / 1000000;  // 每秒钟的计数次数，单位为 M
    reload *= 1000000 / configTICK_RATE_HZ;  // 根据 FreeRTOS 的时钟节拍频率设定溢出时间
    fac_ms = 1000 / configTICK_RATE_HZ;  // 代表操作系统可以延时的最小单位（毫秒）
 
    // 配置 SysTick 中断并启动
    SysTick->CTRL |= SysTick_CTRL_TICKINT_Msk;  // 开启 SysTick 中断
    SysTick->LOAD = reload;  // 设置重装载值
    SysTick->CTRL |= SysTick_CTRL_ENABLE_Msk;  // 开启 SysTick
#else
    // 非操作系统下，计算每毫秒的 SysTick 计数
    fac_ms = (u16)fac_us * 1000;
#endif
}
 
// 延时 n 微秒
// nus: 要延时的微秒数
void delay_us(u32 nus)
{
    u32 ticks;
    u32 told, tnow, tcnt = 0;
    u32 reload = SysTick->LOAD;  // 获取 SysTick 的重装载值
    ticks = nus * fac_us;  // 计算需要的节拍数
 
    told = SysTick->VAL;  // 获取当前 SysTick 计数器的值
    while (1)
    {
        tnow = SysTick->VAL;
        if (tnow != told)
        {
            // 计算经过的节拍数
            if (tnow < told)
                tcnt += told - tnow;  // SysTick 是递减计数器
            else
                tcnt += reload - tnow + told;
            told = tnow;
            if (tcnt >= ticks)
                break;  // 时间超过或等于要延迟的时间，退出循环
        }
    }
}
 
// 延时 n 毫秒
// nms: 要延时的毫秒数
void delay_ms(u32 nms)
{
    // 如果 FreeRTOS 调度器已经启动
    if (xTaskGetSchedulerState() != taskSCHEDULER_NOT_STARTED)
    {
        // 如果延时时间大于操作系统的最小时间周期，则使用 FreeRTOS 的延时函数
        if (nms >= fac_ms)
        {
            vTaskDelay(nms / fac_ms);  // FreeRTOS 延时，不会阻止任务调度
        }
        nms %= fac_ms;  // 剩余时间使用普通方式延时
    }
    delay_us((u32)(nms * 1000));  // 普通方式延时
}
 
// 延时 n 毫秒，不会引起任务调度
// nms: 要延时的毫秒数
void delay_xms(u32 nms)
{
    u32 i;
    for (i = 0; i < nms; i++)
        delay_us(1000);  // 循环调用 delay_us 实现毫秒延时
}
```
以下是改写后的 delay.h 头文件：
```c
#ifndef __DELAY_H
#define __DELAY_H

#include "stm32f10x.h"
#include "FreeRTOS.h"
#include "task.h"

/* 延时函数声明 */
void delay_init(void);                // 延时初始化函数
void delay_us(uint32_t us);           // 微秒级延时
void delay_ms(uint32_t ms);           // 毫秒级延时
void delay_xms(uint32_t ms);          // 封装FreeRTOS中的延时函数

#endif
```
---

*更多内容陆续添加...*
