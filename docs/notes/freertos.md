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

---

*更多内容陆续添加...*
