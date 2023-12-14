#!/bin/bash

# 确保没有该python进程
if pgrep -f "/root/anaconda3/envs/DL/bin/python3.8 main.py --metric processes" > /dev/null; then
  echo "Another instance of the process is already running. Exiting."
  exit 1
fi

# 获取当前可读的时间
timestamp=$(date +"%Y-%m-%d_%H-%M-%S")

# 设置Zilean-Forge的目录
forge_dir="/root/PycharmProjects/Tiny-Zilean-Forge"
logs_dir="$forge_dir/logs"
config_dir="$forge_dir/config"
storage_dir="$forge_dir/storage"

# 如果logs文件夹不存在则创建
if [ ! -d "$logs_dir" ]; then
  mkdir -p "$logs_dir"
fi

# 如果config文件夹不存在则创建
if [ ! -d "$config_dir" ]; then
  mkdir -p "$config_dir"
fi

# 如果storage文件夹不存在则创建
if [ ! -d "$storage_dir" ]; then
  mkdir -p "$storage_dir"
fi

# 切换到合适的目录
cd "$forge_dir"

# 添加trap命令，当脚本退出时执行指定操作
trap "pkill stress-ng" EXIT

# 定义函数，用于检测并重新启动 Python 脚本
start_python_script() {
  while true; do
    /root/anaconda3/envs/DL/bin/python3.8 main.py --metric processes &
    python_pid=$!  # 获取Python进程的PID
    wait $python_pid  # 等待Python进程结束
    python_exit_status=$?  # 保存Python进程的退出状态
    if [ $python_exit_status -eq 0 ]; then
      break
    else
      echo "Python script exited with an error. Restarting in 5 minutes..."
      # 清除可能的残余程序
      pkill python
      pkill stress-ng
      sleep 300
    fi
  done
}

# 启动 Python 脚本
start_python_script
