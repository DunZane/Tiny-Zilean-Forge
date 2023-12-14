import pickle
import psutil
import resource


def get_current_memory_utilization():
    memory = psutil.virtual_memory()
    # 返回已使用的内存，以MB为单位
    return memory.used / (1024 * 1024)


def get_current_cpu_utilization():
    # 返回cpu的使用率
    return psutil.cpu_percent(interval=1)


def get_current_cpu_available():
    # 返回cpu的可用率
    return 100 - psutil.cpu_percent(interval=1)


def save_data_to_file(data, file_path):
    try:
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
        print(f"Data saved to {file_path}")
    except Exception as e:
        print(f"Error: {str(e)}")


def get_timeout_from_cmd(cmd):
    index = cmd.index('--timeout')
    timeout = float(cmd[index + 1])
    return timeout


def get_current_mem_percent():
    # 获取内存使用情况
    mem = psutil.virtual_memory()
    return mem.percent


def get_available_memory():
    memory = psutil.virtual_memory()
    bytes_val = memory.available
    # 最后返回的形式是以M的形式返回
    return bytes_val / (1024 * 1024)


def get_current_processes_num():
    try:
        all_processes = list(psutil.process_iter())
        return len(all_processes)
    except FileNotFoundError as e:
        # 处理FileNotFoundError异常
        print(f"An error occurred: {e}. Check if the required files are accessible.")
        return 20
    except Exception as e:
        print(f"unexpect error occurred: {e}.")
        return 20


# def get_available_processes_num():
#     # 运行 ulimit -u 命令并捕获输出
#     process = subprocess.Popen(['ulimit', '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     output, error = process.communicate()
#
#     # 解析输出，获取进程数量
#     if output:
#         output = output.strip().decode()  # 将字节转换为字符串
#         if output == 'unlimited':
#             max_processes = float('inf')  # 表示无限大
#         else:
#             max_processes = int(output)
#             return max_processes - get_current_processes_num()
#     else:
#         print(f"Error: {error}")


def get_available_processes_num():
    # 获取进程数量限制
    soft, hard = resource.getrlimit(resource.RLIMIT_NPROC)
    if soft == resource.RLIM_INFINITY:
        max_processes = float('inf')  # 表示无限大
    else:
        max_processes = soft
    # Number of fork workers must be between 0 and 4096
    return 4096 - get_current_processes_num()  # 你需要实现 get_current_processes_num() 函数


if __name__ == '__main__':
    print(get_current_cpu_available())
