import concurrent.futures
import datetime
import os
import random
import signal
import subprocess
import time
import yaml
from core.cpu.cmd_factory import CpuCmdGenerator
from core.generator import DriftGenerator
from core.mem.cmd_factory import MemCmdGenerator
from core.processes.cmd_factory import ProcessesGenerator
from core.toolkit.logger import setup_logger
from core.toolkit.pools import perform_insert
from core.toolkit.tools import (get_timeout_from_cmd, get_current_cpu_utilization,
                                get_current_memory_utilization, get_current_processes_num)

# 加载配置相关信息
with open('config/scheduler_config.yaml', 'r') as file:
    config = yaml.safe_load(file)


config_scheduler = config['settings']['scheduler']


class Scheduler:
    def __init__(self, metric):
        # 获取当前时间的纳秒级时间戳，确保足够随机
        current_time_ns = int(time.time_ns())
        random.seed(current_time_ns)
        # 指标
        self.metric = metric
        self.sum_event = 0
        self.logger = setup_logger("scheduler")

        # 主漂移之间间隔
        self.interval = config_scheduler['event_interval'][0]
        # 子漂移之间隔离
        self.sub_interval = config_scheduler['sub_event_interval'][0]
        # 子漂移个数
        self.sub_drift = config_scheduler['sub_drift'][0]
        # 主漂移与子漂移之间的距离
        self.father_sub_interval = config_scheduler['father_sub_interval']
        # 独立漂移的持续事件
        self.new_time_span = config_scheduler['new_distribution_time_span'][0]

    def start(self):
        datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        dg = DriftGenerator()

        if self.metric == 'cpu':
            sg = CpuCmdGenerator()
        elif self.metric == 'mem':
            sg = MemCmdGenerator()
        elif self.metric == 'processes':
            sg = ProcessesGenerator()
        else:
            raise ValueError("Unknown metric")

        while True:
            # 获取漂移类型生成器
            drift_parameters = dg.generate_drift_parameters()
            # 获取漂移类型
            drift_type = drift_parameters['type']
            # 获取脚本生成器
            cmds, duration, load = sg.generate_script(drift_parameters)
            if drift_type in ["Sudden", "Incremental", "Gradual"]:
                # 较长漂移
                mode = drift_parameters['mode']
                if mode == 'transmitted drift':
                    # 传递漂移(transmitted drift)：这种模式下会在新分布下继续生成新漂移
                    start_time = self._handle_transmitted_drift(drift_type, cmds, duration, load, sg)
                else:

                    # 独立漂移(independent drift)：新分布上不会再发生漂移
                    span = random.uniform(self.new_time_span['lower'], self.new_time_span['higher'])
                    start_time = self._handle_independent_drift(drift_type, cmds, duration, load, span)

                self._handle_final_sudden_drift(start_time)
            else:
                # 较短漂移
                self._handler_short_drift(drift_type, cmds)
            self.sum_event += 1
            # 任务与任务之间隔离，这个参数后期可以配置，另外这个配置区间尽量大一些
            event_interval = random.uniform(self.interval['lower'], self.interval['higher'])
            self.logger.info("已经生成{}个漂移".format(self.sum_event))
            time.sleep(event_interval)

    def _start_incremental(self, cmds, duration, load):
        """
        创建类型为Incremental的漂移
        :param cmds: 创建的命令集合
        :param duration: 每个命令的间隔时间
        :param load: CPU的目标使用率
        :return: 返回进程列表和开始、结束时间
        """
        # 记录启动时间
        start_time = datetime.datetime.now()

        # 开启进程的命令
        processes = []
        self.logger.info(f"Incremental command: {cmds}")
        for cmd in cmds:
            try:
                process = subprocess.Popen(cmd)
                processes.append(process)
                time.sleep(duration)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Error occurred during subprocess command {cmd} execution: {e}")
            except Exception as e:
                self.logger.error(f"An unexpected error occurred during subprocess command {cmd} execution: {e}")
        end_time = self._get_end_time(load)
        return processes, (start_time, end_time)

    def _start_sudden(self, cmds, load) -> \
            (subprocess.Popen, (datetime.datetime, datetime.datetime)):
        """
        创建类型为Sudden的漂移
        :param cmds: 创建的命令集合
        :param load: cpu的目标使用率
        :return: 返回进程列表和开始、结束时间
        """
        # 记录启动时间
        start_time = datetime.datetime.now()
        cmd = cmds[0]

        # 开启进程的命令
        process = None
        try:
            self.logger.info(f"Sudden commands: {cmd}")
            process = subprocess.Popen(cmd)
        except subprocess.CalledProcessError as e:
            self.logger.error(
                f"Error occurred during subprocess command {cmd} execution: {e}")
        except Exception as e:
            self.logger.error(
                f"An unexpected error occurred during subprocess command {cmd} execution: {e}")
        finally:
            end_time = self._get_end_time(load)
        return process, (start_time, end_time)

    def _start_gradual(self, cmds, duration, load) -> \
            (subprocess.Popen, (datetime.datetime, datetime.datetime)):
        """
        创建类型为gradual的漂移
        :param cmds: 创建的命令集
        :param duration: gradual漂移中位于原始分布的时间段
        :param load: cpu的目标使用率
        :return: 返回进程列表和开始、结束时间
        """
        # 记录启动时间
        start_time = datetime.datetime.now()

        # 开启进程命令
        self.logger.info(f"Gradual command: {cmds}")
        for i, cmd in enumerate(cmds):
            try:
                process = subprocess.Popen(cmd)
                if i == len(cmds) - 1:
                    end_time = self._get_end_time(load)
                    return process, (start_time, end_time)
                else:
                    process.wait()
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Error occurred during subprocess sub command {cmd} execution: {e}")
            except Exception as e:
                self.logger.error(
                    f"An unexpected error occurred during subprocess sub command {cmd} execution: {e}")
            finally:
                time.sleep(duration[i])

    def _sub_drift(self, cmds, sub_events) -> None:
        """
        执行子漂移的cmd命令
        :param cmds: 子漂移的cmd命令
        :param sub_events: cmds每一个cmd对应的漂移事件类型
        :return: 无返回，所有的子漂移运行后都会结束不返回process对象
        """
        # 执行子事件对应的命令
        for i, cmd in enumerate(cmds):
            try:
                self.logger.info(f"Sub {sub_events[i]} commands: {cmd}")
                start_time = datetime.datetime.now()
                process = subprocess.Popen(cmd)
                process.wait()
                span_time = get_timeout_from_cmd(cmds[0])
                end_time = start_time + datetime.timedelta(seconds=span_time)
                # 记录生成的信息,数据记录到数据库中
                drift_info_time = (start_time, end_time)
                perform_insert([sub_events[i], drift_info_time], self.metric)
                self.sum_event += 1

            except subprocess.CalledProcessError as e:
                self.logger.error(f"Error occurred during subprocess sub command {cmd} execution: {e}")
            except Exception as e:
                self.logger.error(
                    f"An unexpected error occurred during subprocess sub command {cmd} execution: {e}")
            finally:
                time.sleep(random.uniform(self.sub_interval['lower'], self.sub_interval['higher']))

    def _handle_transmitted_drift(self, drift_type, cmds, duration, load, sg) -> datetime.datetime:
        """
        作为一个传递漂移，在其稳定基础上还会出现新的漂移
        :param drift_type: 漂移类型，仅包括Sudden、Incremental、Gradual
        :param cmds: 对应执行的命令集
        :param duration: 漂移中断时间
        :param load: 目标cpu负载
        :param sub_cmds: 子漂移cmd集合
        :param sub_events: 子漂移对应的漂移类型事件
        :return: 父漂移结束事件
        """
        if drift_type == "Sudden":
            father_process, drift_info_time = self._start_sudden(cmds, load)
            if father_process is not None:
                # 记录生成的信息,数据记录到数据库中
                perform_insert([drift_type, drift_info_time], self.metric)
            # 子进程与父进程之间需要一定的间隔
            time.sleep(self.father_sub_interval)
            # 创建子事件
            num_sub_events = random.randint(self.sub_drift['lower'], self.sub_drift['higher'])
            sub_cmds, sub_events = sg.generate_sub_script(num_sub_events)
            # 子进程负载:这里可能会持续比较久的一段时间
            self._sub_drift(sub_cmds, sub_events)
            # 处理完后结束父进程
            start_time = datetime.datetime.now()
            if father_process is not None:
                pid = father_process.pid
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError as e:
                    print(f"Error: {e}. Process with PID {pid} does not exist when handle cmds{cmds}")
        elif drift_type == "Incremental":
            father_processes, drift_info_time = self._start_incremental(cmds, duration, load)
            if len(father_processes) > 0:
                # 记录生成的信息,数据记录到数据库中
                perform_insert([drift_type, drift_info_time], self.metric)
            # 子进程与父进程之间需要一定的间隔: incremental的时间再增长一些
            time.sleep(self.father_sub_interval + 400)
            # 创建子事件
            num_sub_events = random.randint(self.sub_drift['lower'], self.sub_drift['higher'])
            sub_cmds, sub_events = sg.generate_sub_script(num_sub_events)
            # 开启子进程
            self._sub_drift(sub_cmds, sub_events)
            # 处理完结束父进程
            start_time = datetime.datetime.now()
            for f_process in father_processes:
                if father_processes is None:
                    continue
                pid = f_process.pid
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError as e:
                    print(f"Error: {e}. Process with PID {pid} does not exist when handle cmds{cmds}")
        else:
            father_process, drift_info_time = self._start_gradual(cmds, duration, load)
            if father_process is not None:
                # 记录生成的信息,数据记录到数据库中
                perform_insert([drift_type, drift_info_time], self.metric)
            # 子进程与父进程之间需要一定的间隔
            time.sleep(self.father_sub_interval)
            # 创建子事件
            num_sub_events = random.randint(self.sub_drift['lower'], self.sub_drift['higher'])
            sub_cmds, sub_events = sg.generate_sub_script(num_sub_events)
            # 开启子进程
            self._sub_drift(sub_cmds, sub_events)
            # 处理完成后的父进程
            start_time = datetime.datetime.now()
            if father_process is not None:
                pid = father_process.pid
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError as e:
                    print(f"Error: {e}. Process with PID {pid} does not exist when handle cmds{cmds}")

        return start_time

    def _handle_independent_drift(self, drift_type, cmds, duration, load, time_span) -> datetime:
        """
        作为一个独立的长期漂移，不会在其基础上再产生新漂移
        :param drift_type: 漂移类型，仅包括Sudden、Incremental、Gradual
        :param cmds: 对应执行的命令集
        :param duration: 漂移中断时间
        :param load: 目标cpu负载
        :param time_span: 在稳定分布上持续的时间
        :return: 漂移结束事件
        """
        if drift_type == "Sudden":
            father_process, drift_info_time = self._start_sudden(cmds, load)
            if father_process is not None:
                # 记录生成的信息,数据记录到数据库中
                perform_insert([drift_type, drift_info_time], self.metric)
            # 位于新分布所持续的时间
            time.sleep(time_span)
            # 处理完后结束父进程
            start_time = datetime.datetime.now()
            if father_process is not None:
                pid = father_process.pid
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError as e:
                    print(f"Error: {e}. Process with PID {pid} does not exist when handle cmds{cmds}")

        elif drift_type == "Incremental":
            father_processes, drift_info_time = self._start_incremental(cmds, duration, load)
            if len(father_processes) > 0:
                # 记录生成的信息,数据记录到数据库中
                perform_insert([drift_type, drift_info_time], self.metric)
            # 位于新分布所持续的时间：incremental的时间再增长一些
            time.sleep(time_span)
            # 处理完结束父进程
            start_time = datetime.datetime.now()
            for f_process in father_processes:
                if father_processes is None:
                    continue
                pid = f_process.pid
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError as e:
                    print(f"Error: {e}. Process with PID {pid} does not exist when handle cmds{cmds}")

        else:
            father_process, drift_info_time = self._start_gradual(cmds, duration, load)
            if father_process is not None:
                # 记录生成的信息,数据记录到数据库中
                perform_insert([drift_type, drift_info_time], self.metric)
            time.sleep(time_span)
            # 处理完后结束父进程
            start_time = datetime.datetime.now()
            if father_process is not None:
                pid = father_process.pid
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError as e:
                    print(f"Error: {e}. Process with PID {pid} does not exist when handle cmds{cmds}")

        return start_time

    def _handler_short_drift(self, drift_type, cmds) -> None:
        """
        调度短期漂移的命令
        :param drift_type: 漂移类型，只有Blip、Recurrent类型的漂移
        :param cmds: 创建的命令集合
        :return: 无返回
        """
        # 记录启动时间
        start_time = datetime.datetime.now()
        cmd = cmds[0]

        # 开启进程的命令
        try:
            self.logger.info(f"{drift_type} command: {cmd}")
            process = subprocess.Popen(cmd)
            process.wait()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error occurred during subprocess sub command {cmd} execution: {e}")
        except Exception as e:
            self.logger.error(
                f"An unexpected error occurred during subprocess sub command {cmd} execution: {e}")
        finally:
            # 获取进程消耗时间
            span_time = get_timeout_from_cmd(cmd)
            end_time = start_time + datetime.timedelta(seconds=span_time)
            # 记录生成的信息,数据记录到数据库中
            drift_info_time = (start_time, end_time)
            perform_insert([drift_type, drift_info_time], self.metric)

    def _handle_final_sudden_drift(self, start_time) -> None:
        """
        针对长度漂移最后在尾部添加Sudden类型的漂移
        :param start_time: 漂移开始的时间
        :return: 无返回
        """
        end_time = datetime.datetime.now()
        # 记录生成的信息,数据记录到数据库中
        drift_info_time = (start_time, end_time)
        perform_insert(["Sudden", drift_info_time], self.metric)

    def _get_end_time(self, target) -> datetime.datetime:
        """
        通过检查指定指标是否到达目前值来获取cmd运行结束事件
        :param target: 指标目标值
        :return: 指标到达目标值的时刻
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            count = 0
            max_count = 50  # Set the maximum number of attempts
            wait_time = 5  # Set the wait time in seconds
            while count < max_count:
                if self.metric == 'cpu':
                    future = executor.submit(Scheduler._check_cpu_utilization, target)
                elif self.metric == 'mem':
                    future = executor.submit(Scheduler._check_memory_utilization, target)
                elif self.metric == 'processes':
                    future = executor.submit(Scheduler._check_processes_utilization, target)
                try:
                    result = future.result()
                    if result:
                        return datetime.datetime.now()
                except concurrent.futures.TimeoutError:
                    self.logger.warning('Timeout occurred in _get_end_time function.')
                except FileNotFoundError as e:
                    self.logger.warning(f'FileNotFoundError occurred: {e}.')
                except Exception as e:
                    self.logger.error(f'An unexpected error occurred: {e}.')
                count += 1
                time.sleep(wait_time)
            self.logger.warning('Maximum attempts reached in _get_end_time function.')
            return datetime.datetime.now()

    @staticmethod
    def _check_cpu_utilization(target) -> bool:
        """
        检查当前机器的cpu使用率是否达到目标值
        :param target: cpu使用率目标值
        :return: 返回true or false
        """
        cpu_utilization = get_current_cpu_utilization()
        return cpu_utilization >= float(target)

    @staticmethod
    def _check_memory_utilization(target) -> bool:
        """
        检查当前机器的mem active是否达到目标值
        :param target: mem使用率目标值
        :return: 返回true or false
        """
        mem_utilization = get_current_memory_utilization()
        return mem_utilization >= float(target)

    @staticmethod
    def _check_processes_utilization(target) -> bool:
        """
        检查到当前机器的进程数是否达到目标值
        :param target: 当前机器目标值
        :return: 返回true or false
        """
        processes_count = get_current_processes_num()
        return processes_count >= float(target)
