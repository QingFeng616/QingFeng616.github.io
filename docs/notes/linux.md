# Linux 嵌入式开发学习

> 专注于嵌入式Linux开发的实战指南 - 持续更新中...

---

## 基础命令

### 文件操作

```bash
ls          # 列出文件
ls -l       # 详细列表格式
ls -a       # 显示所有文件（包括隐藏文件）
ls -lh      # 人性化显示文件大小
cd          # 切换目录
cd ..       # 返回上一级目录
cd ~        # 回到用户主目录
cd -        # 回到上一次所在目录
pwd         # 显示当前路径
cp file1 file2   # 复制文件1到文件2
cp -r dir1 dir2  # 递归复制目录
mv file1 file2   # 移动/重命名文件
rm file     # 删除文件
rm -r dir   # 递归删除目录
rm -f file  # 强制删除（不提示）
mkdir dir   # 创建目录
mkdir -p dir/subdir  # 递归创建多级目录
touch file  # 创建空文件或更新文件时间戳
cat file    # 查看文件内容
cat file1 file2 > file3  # 合并文件1和文件2到文件3
tail file   # 查看文件末尾10行
tail -f file  # 实时查看文件更新
head file   # 查看文件开头10行
less file   # 分页查看文件内容（按q退出）
more file   # 分页查看文件内容
```

### 系统信息

```bash
uname -a    # 系统内核信息
uname -r    # 内核版本
cat /etc/os-release  # 发行版信息
hostname    # 主机名
date        # 显示当前时间
time        # 显示命令执行时间
top         # 实时进程监控（按q退出）
htop        # 增强型进程监控（需安装）
df -h       # 磁盘使用情况（人性化显示）
du -sh dir  # 查看目录大小
free -h     # 内存使用情况
whoami      # 当前用户
who         # 登录用户信息
last        # 最近登录历史
```

---

## 用户与权限

### 用户管理

```bash
useradd username  # 创建用户
userdel username  # 删除用户
usermod -aG group username  # 将用户添加到组
passwd username   # 修改用户密码
su username       # 切换用户
sudo command      # 以管理员权限执行命令
```

### 权限管理

```bash
chmod 755 file    # 设置文件权限为rwxr-xr-x
chmod +x file     # 添加执行权限
chmod -R 777 dir  # 递归设置目录权限
chown user:group file  # 修改文件所有者和组
chown -R user:group dir  # 递归修改目录所有者
```

---

## 网络命令

```bash
ifconfig    # 查看网络接口信息（传统命令）
ip addr     # 查看网络接口信息（新命令）
ping host   # 测试网络连通性
ping -c 4 host  # 发送4个包后停止
curl url    # 下载网页内容
wget url    # 下载文件
netstat -tulpn  # 查看监听端口
ss -tulpn   # 查看监听端口（新命令）
traceroute host  # 跟踪路由路径
mtr host    # 结合ping和traceroute的工具
ssh user@host    # 远程登录
scp file user@host:/path  # 远程复制文件
```

---

## 进程管理

```bash
ps aux      # 查看所有进程
ps aux | grep process  # 查找特定进程
kill pid    # 终止进程
kill -9 pid # 强制终止进程
pkill process_name  # 根据进程名终止进程
pgrep process_name  # 根据进程名查找PID
nohup command &    # 后台运行命令（退出终端后继续运行）
command &   # 后台运行命令（退出终端后停止）
jobs        # 查看后台作业
fg %1       # 将后台作业1调到前台
```

---

## 压缩与解压

```bash
tar -czvf archive.tar.gz dir  # 压缩目录为tar.gz
tar -xzvf archive.tar.gz      # 解压tar.gz
tar -cjvf archive.tar.bz2 dir # 压缩目录为tar.bz2
tar -xjvf archive.tar.bz2     # 解压tar.bz2
zip archive.zip file1 file2   # 压缩为zip
unzip archive.zip             # 解压zip
```

---

## 文本处理

```bash
grep pattern file  # 在文件中查找匹配模式
grep -i pattern file  # 忽略大小写
grep -r pattern dir   # 递归查找目录
awk '{print $1}' file  # 打印文件第一列
sort file  # 排序文件内容
sort -n file  # 按数字排序
uniq file  # 去除重复行（需先排序）
wc -l file  # 统计文件行数
wc -w file  # 统计文件单词数
wc -c file  # 统计文件字符数
```

---

## 实用技巧

### 历史命令

```bash
history     # 查看命令历史
!100        # 执行历史中第100条命令
!ls         # 执行最近一次以ls开头的命令
Ctrl + R    # 搜索历史命令
```

### 快捷键

```bash
Ctrl + C    # 终止当前命令
Ctrl + D    # 退出当前会话
Ctrl + L    # 清屏
Ctrl + A    # 移动到命令行开头
Ctrl + E    # 移动到命令行结尾
Ctrl + U    # 删除光标前的内容
Ctrl + K    # 删除光标后的内容
Ctrl + W    # 删除光标前的单词
```

### 其他技巧

```bash
> file       # 清空文件内容
command > file  # 将命令输出重定向到文件（覆盖）
command >> file # 将命令输出追加到文件
command1 | command2  # 将command1的输出作为command2的输入
```

---

---

## 嵌入式Linux核心专题

### 1. 交叉编译环境搭建

```bash
# 安装交叉编译工具链
sudo apt-get install gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf

# 验证工具链
arm-linux-gnueabihf-gcc --version

# 设置环境变量
export ARCH=arm
export CROSS_COMPILE=arm-linux-gnueabihf-
export PATH=$PATH:/path/to/toolchain/bin
```

### 2. 内核与驱动开发基础

```bash
# 配置内核（基于ARM架构）
make ARCH=arm menuconfig
make ARCH=arm xilinx_zynq_defconfig  # 针对Xilinx Zynq平台

# 编译内核
make ARCH=arm -j$(nproc) uImage
make ARCH=arm -j$(nproc) modules

# 编译设备树
make ARCH=arm dtbs

# 安装模块到根文件系统
make ARCH=arm INSTALL_MOD_PATH=/path/to/rootfs modules_install
```

### 3. 根文件系统构建

```bash
# 使用BusyBox构建最小根文件系统
git clone git://busybox.net/busybox.git
cd busybox
make menuconfig  # 选择静态编译(Build static binary)
make -j$(nproc)
make install CONFIG_PREFIX=/path/to/rootfs

# 创建必要的目录结构
cd /path/to/rootfs
mkdir -p dev proc sys etc etc/init.d lib

# 编写初始化脚本（etc/init.d/rcS）
cat > etc/init.d/rcS << EOF
#!/bin/sh
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev
/sbin/mdev -s
ifconfig eth0 192.168.1.100 netmask 255.255.255.0 up
route add default gw 192.168.1.1
EOF
chmod +x etc/init.d/rcS

# 制作根文件系统镜像
dd if=/dev/zero of=rootfs.ext4 bs=1M count=128
sudo mkfs.ext4 rootfs.ext4
sudo mkdir -p /mnt/rootfs
sudo mount rootfs.ext4 /mnt/rootfs
sudo cp -r /path/to/rootfs/* /mnt/rootfs/
sudo umount /mnt/rootfs
```

### 4. 设备树（Device Tree）操作

```bash
# 查看当前设备树
cat /proc/device-tree/model
cat /proc/device-tree/compatible

# 编译设备树源文件
dtc -I dts -O dtb -o myboard.dtb myboard.dts

# 反编译设备树二进制文件
dtc -I dtb -O dts -o myboard.dts myboard.dtb

# 在U-Boot中指定设备树
setenv bootargs 'console=ttyPS0,115200 root=/dev/mmcblk0p2 rootfstype=ext4 rw'
setenv bootcmd 'mmc dev 0; mmc read 0x00000000 0x1000 0x800; mmc read 0x00A00000 0x1800 0x200; bootz 0x00000000 - 0x00A00000'
saveenv
```

### 5. 系统调试工具

```bash
# 串口调试工具
sudo apt-get install minicom screen
minicom -s  # 配置串口参数（波特率115200，8N1）
screen /dev/ttyUSB0 115200

# 硬件调试
apt-get install gdb-multiarch
arm-linux-gnueabihf-gdb vmlinux  # 内核调试

# 性能分析
perf list  # 查看可用性能事件
perf top -g  # 实时性能分析
perf record -g -p <pid>  # 记录进程性能数据
perf report  # 分析性能数据

# 内存调试
valgrind --leak-check=full ./application  # 用户态内存泄漏检测
cat /proc/meminfo  # 查看内存使用详情
cat /proc/<pid>/maps  # 查看进程内存映射
```

### 6. 嵌入式应用开发

```c
// 示例：LED驱动应用（用户态控制GPIO）
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>

#define GPIO_PATH "/sys/class/gpio/gpio123/"

int main() {
    int fd;
    
    // 导出GPIO
    fd = open("/sys/class/gpio/export", O_WRONLY);
    write(fd, "123", 3);
    close(fd);
    
    // 设置为输出模式
    fd = open(GPIO_PATH "direction", O_WRONLY);
    write(fd, "out", 3);
    close(fd);
    
    // 控制LED闪烁
    fd = open(GPIO_PATH "value", O_WRONLY);
    while(1) {
        write(fd, "1", 1);
        sleep(1);
        write(fd, "0", 1);
        sleep(1);
    }
    close(fd);
    
    // 取消导出GPIO
    fd = open("/sys/class/gpio/unexport", O_WRONLY);
    write(fd, "123", 3);
    close(fd);
    
    return 0;
}
```

```bash
# 交叉编译应用程序
arm-linux-gnueabihf-gcc -o led_control led_control.c -static

# 传输到开发板
scp led_control root@192.168.1.100:/root/

# 在开发板上运行
chmod +x led_control
./led_control
```

### 7. 启动流程分析

```bash
# U-Boot阶段
printenv  # 查看环境变量
version  # 查看U-Boot版本
bdinfo   # 查看板级信息

# 内核启动阶段
cat /proc/cmdline  # 查看内核启动参数
dmesg | head -50  # 查看内核启动日志
dmesg | grep "error\|warn"  # 查找启动错误

# 用户空间初始化
ls -l /etc/init.d/  # 查看初始化脚本
ps aux | grep init  # 查看init进程
cat /etc/inittab    # 查看SysV init配置
```

---

## 嵌入式Shell脚本实战

### 1. 自动测试脚本

```bash
#!/bin/bash
# GPIO功能自动化测试脚本

GPIO_NUM="123"
TEST_COUNT=5

# 导出GPIO
echo $GPIO_NUM > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio$GPIO_NUM/direction

echo "Starting GPIO test..."
for ((i=1; i<=TEST_COUNT; i++))
do
    echo "1" > /sys/class/gpio/gpio$GPIO_NUM/value
    echo "Test $i: GPIO set to HIGH"
    sleep 1
    
    echo "0" > /sys/class/gpio/gpio$GPIO_NUM/value
    echo "Test $i: GPIO set to LOW"
    sleep 1
done

# 清理
echo $GPIO_NUM > /sys/class/gpio/unexport
echo "Test completed successfully"
```

### 2. 系统监控脚本

```bash
#!/bin/bash
# 嵌入式系统资源监控脚本

INTERVAL=5
LOG_FILE="system_monitor.log"

echo "System Monitor started at $(date)" > $LOG_FILE

trap "echo 'Monitor stopped at $(date)' >> $LOG_FILE; exit" INT

while true
do
    echo "=== $(date) ===" >> $LOG_FILE
    echo "CPU Usage:" >> $LOG_FILE
    top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1 "% used"}' >> $LOG_FILE
    echo "Memory Usage:" >> $LOG_FILE
    free -m | awk '/Mem:/ {print $3"MB used / "$2"MB total ("$3/$2*100"%)"}' >> $LOG_FILE
    echo "Disk Usage:" >> $LOG_FILE
    df -h / | awk '/\// {print $3" used / "$2" total ("$5")"}' >> $LOG_FILE
    echo "Network Status:" >> $LOG_FILE
    ifconfig eth0 | grep "inet addr" >> $LOG_FILE
    echo >> $LOG_FILE
    
    sleep $INTERVAL
done
```

---

## 高级命令组合技巧

### 1. 批量文件处理

```bash
# 批量交叉编译当前目录下所有C文件
for file in *.c; do
    arm-linux-gnueabihf-gcc -o "${file%.c}" "$file" -static
done

# 批量传输文件到开发板
scp *.bin root@192.168.1.100:/root/

# 批量修改文件权限
find /path/to/binaries -type f -name "*.sh" -exec chmod +x {} \;
```

### 2. 日志分析与过滤

```bash
# 从串口日志中提取内核启动时间
dmesg | grep "Linux version" | awk '{print $3, $4, $5}'

# 统计系统启动过程中的驱动加载情况
dmesg | grep "driver loaded" | wc -l

# 实时监控串口日志中的错误信息
screen /dev/ttyUSB0 115200 | tee serial.log | grep -i "error\|fail\|warn"
```

### 3. 硬件信息采集

```bash
# 采集CPU温度（针对不同平台）
cat /sys/class/thermal/thermal_zone0/temp  # 通用方式
cat /sys/devices/virtual/thermal/thermal_zone0/temp  # ARM平台

# 查看GPIO状态
for gpio in /sys/class/gpio/gpio*
do
    echo "$(basename $gpio): $(cat $gpio/value) ($(cat $gpio/direction))"
done

# 查看SPI设备
ls -l /dev/spidev*
cat /sys/class/spi_master/spi0/device/modalias
```

---

## 常见问题排查

### 1. 启动失败排查流程

```bash
# 检查U-Boot是否正常启动
echo "U-Boot version: $(version)"

# 检查SD卡/MMC设备
mmc list
mmc dev 0
mmc read 0x0 0x100 0x10  # 读取MBR

# 检查内核镜像
md5sum uImage  # 计算镜像MD5值
cmp uImage /dev/mmcblk0p1  # 对比存储中的镜像
```

### 2. 网络问题排查

```bash
# 检查物理连接
ethtool eth0  # 查看网卡状态
mii-tool eth0  # 查看PHY状态

# 检查IP配置
ip addr show eth0
route -n
cat /etc/resolv.conf

# 网络连通性测试
ping -c 3 8.8.8.8
curl -I http://www.baidu.com
```

---

*嵌入式Linux进阶内容持续更新中...*