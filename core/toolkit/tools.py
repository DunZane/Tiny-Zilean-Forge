import pickle
import psutil
import resource


def get_current_memory_utilization():
    memory = psutil.virtual_memory()
    # Return used memory in MB
    return memory.used / (1024 * 1024)


def get_current_cpu_utilization():
    # Return CPU utilization
    return psutil.cpu_percent(interval=1)


def get_current_cpu_available():
    # Return CPU availability
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
    # Get memory usage
    mem = psutil.virtual_memory()
    return mem.percent


def get_available_memory():
    memory = psutil.virtual_memory()
    bytes_val = memory.available
    # Return available memory in MB
    return bytes_val / (1024 * 1024)


def get_current_processes_num():
    try:
        all_processes = list(psutil.process_iter())
        return len(all_processes)
    except FileNotFoundError as e:
        # Handle FileNotFoundError exception
        print(f"An error occurred: {e}. Check if the required files are accessible.")
        return 20
    except Exception as e:
        print(f"Unexpected error occurred: {e}.")
        return 20


# def get_available_processes_num():
#     # Run ulimit -u command and capture output
#     process = subprocess.Popen(['ulimit', '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     output, error = process.communicate()
#
#     # Parse output to get the number of processes
#     if output:
#         output = output.strip().decode()  # Convert bytes to string
#         if output == 'unlimited':
#             max_processes = float('inf')  # Represent infinity
#         else:
#             max_processes = int(output)
#             return max_processes - get_current_processes_num()
#     else:
#         print(f"Error: {error}")


def get_available_processes_num():
    # Get process limit
    soft, hard = resource.getrlimit(resource.RLIMIT_NPROC)
    if soft == resource.RLIM_INFINITY:
        max_processes = float('inf')  # Represent infinity
    else:
        max_processes = soft
    # Number of fork workers must be between 0 and 4096
    return 4096 - get_current_processes_num()  # You need to implement get_current_processes_num() function


if __name__ == '__main__':
    print(get_current_cpu_available())
