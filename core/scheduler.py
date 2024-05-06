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

# Load configuration information
with open('config/scheduler_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

config_scheduler = config['settings']['scheduler']


class Scheduler:
    def __init__(self, metric):
        # Ensure sufficient randomness by using the current time in nanoseconds as seed
        current_time_ns = int(time.time_ns())
        random.seed(current_time_ns)

        # Metric and initialization
        self.metric = metric
        self.sum_event = 0
        self.logger = setup_logger("scheduler")

        # Main drift interval
        self.interval = config_scheduler['event_interval'][0]
        # Sub-drift isolation interval
        self.sub_interval = config_scheduler['sub_event_interval'][0]
        # Number of sub-drifts
        self.sub_drift = config_scheduler['sub_drift'][0]
        # Interval between main and sub-drifts
        self.father_sub_interval = config_scheduler['father_sub_interval']
        # Duration of independent drift events
        self.new_time_span = config_scheduler['new_distribution_time_span'][0]

    def start(self):
        datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        dg = DriftGenerator()

        # Initialize the appropriate command generator based on the metric
        if self.metric == 'cpu':
            sg = CpuCmdGenerator()
        elif self.metric == 'mem':
            sg = MemCmdGenerator()
        elif self.metric == 'processes':
            sg = ProcessesGenerator()
        else:
            raise ValueError("Unknown metric")

        while True:
            # Generate drift parameters
            drift_parameters = dg.generate_drift_parameters()
            drift_type = drift_parameters['type']
            cmds, duration, load = sg.generate_script(drift_parameters)
            if drift_type in ["Sudden", "Incremental", "Gradual"]:
                mode = drift_parameters['mode']
                if mode == 'transmitted drift':
                    start_time = self._handle_transmitted_drift(drift_type, cmds, duration, load, sg)
                else:
                    span = random.uniform(self.new_time_span['lower'], self.new_time_span['higher'])
                    start_time = self._handle_independent_drift(drift_type, cmds, duration, load, span)
                self._handle_final_sudden_drift(start_time)
            else:
                self._handler_short_drift(drift_type, cmds)
            self.sum_event += 1
            event_interval = random.uniform(self.interval['lower'], self.interval['higher'])
            self.logger.info("Generated {} drift events".format(self.sum_event))
            time.sleep(event_interval)

    def _start_incremental(self, cmds, duration, load):
        """
        Create Incremental type drifts
        """
        start_time = datetime.datetime.now()
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

    def _start_sudden(self, cmds, load):
        """
        Create Sudden type drifts
        """
        start_time = datetime.datetime.now()
        cmd = cmds[0]
        process = None
        try:
            self.logger.info(f"Sudden commands: {cmd}")
            process = subprocess.Popen(cmd)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error occurred during subprocess command {cmd} execution: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during subprocess command {cmd} execution: {e}")
        finally:
            end_time = self._get_end_time(load)
        return process, (start_time, end_time)

    def _start_gradual(self, cmds, duration, load):
        """
        Create Gradual type drifts
        """
        start_time = datetime.datetime.now()
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
                self.logger.error(f"An unexpected error occurred during subprocess sub command {cmd} execution: {e}")
            finally:
                time.sleep(duration[i])

    def _sub_drift(self, cmds, sub_events):
        """
        Execute sub-drift commands
        """
        for i, cmd in enumerate(cmds):
            try:
                self.logger.info(f"Sub {sub_events[i]} commands: {cmd}")
                start_time = datetime.datetime.now()
                process = subprocess.Popen(cmd)
                process.wait()
                span_time = get_timeout_from_cmd(cmds[0])
                end_time = start_time + datetime.timedelta(seconds=span_time)
                drift_info_time = (start_time, end_time)
                perform_insert([sub_events[i], drift_info_time], self.metric)
                self.sum_event += 1
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Error occurred during subprocess sub command {cmd} execution: {e}")
            except Exception as e:
                self.logger.error(f"An unexpected error occurred during subprocess sub command {cmd} execution: {e}")
            finally:
                time.sleep(random.uniform(self.sub_interval['lower'], self.sub_interval['higher']))

    def _handle_transmitted_drift(self, drift_type, cmds, duration, load, sg):
        """
        Handle transmitted drift events
        """
        if drift_type == "Sudden":
            father_process, drift_info_time = self._start_sudden(cmds, load)
            if father_process is not None:
                perform_insert([drift_type, drift_info_time], self.metric)
            time.sleep(self.father_sub_interval)
            num_sub_events = random.randint(self.sub_drift['lower'], self.sub_drift['higher'])
            sub_cmds, sub_events = sg.generate_sub_script(num_sub_events)
            self._sub_drift(sub_cmds, sub_events)
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
                perform_insert([drift_type, drift_info_time], self.metric)
            time.sleep(self.father_sub_interval + 400)
            num_sub_events = random.randint(self.sub_drift['lower'], self.sub_drift['higher'])
            sub_cmds, sub_events = sg.generate_sub_script(num_sub_events)
            self._sub_drift(sub_cmds, sub_events)
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
                perform_insert([drift_type, drift_info_time], self.metric)
            time.sleep(self.father_sub_interval)
            num_sub_events = random.randint(self.sub_drift['lower'], self.sub_drift['higher'])
            sub_cmds, sub_events = sg.generate_sub_script(num_sub_events)
            self._sub_drift(sub_cmds, sub_events)
            start_time = datetime.datetime.now()
            if father_process is not None:
                pid = father_process.pid
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError as e:
                    print(f"Error: {e}. Process with PID {pid} does not exist when handle cmds{cmds}")
        return start_time

    def _handle_independent_drift(self, drift_type, cmds, duration, load, time_span):
        """
        Handle independent drift events
        """
        if drift_type == "Sudden":
            father_process, drift_info_time = self._start_sudden(cmds, load)
            if father_process is not None:
                perform_insert([drift_type, drift_info_time], self.metric)
            time.sleep(time_span)
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
                perform_insert([drift_type, drift_info_time], self.metric)
            time.sleep(time_span)
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
                perform_insert([drift_type, drift_info_time], self.metric)
            time.sleep(time_span)
            start_time = datetime.datetime.now()
            if father_process is not None:
                pid = father_process.pid
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError as e:
                    print(f"Error: {e}. Process with PID {pid} does not exist when handle cmds{cmds}")
        return start_time

    def _handler_short_drift(self, drift_type, cmds):
        """
        Handle short-term drift commands
        """
        start_time = datetime.datetime.now()
        cmd = cmds[0]
        try:
            self.logger.info(f"{drift_type} command: {cmd}")
            process = subprocess.Popen(cmd)
            process.wait()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error occurred during subprocess sub command {cmd} execution: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during subprocess sub command {cmd} execution: {e}")
        finally:
            span_time = get_timeout_from_cmd(cmd)
            end_time = start_time + datetime.timedelta(seconds=span_time)
            drift_info_time = (start_time, end_time)
            perform_insert([drift_type, drift_info_time], self.metric)

    def _handle_final_sudden_drift(self, start_time):
        """
        Handle final sudden drift at the end of longer drifts
        """
        end_time = datetime.datetime.now()
        drift_info_time = (start_time, end_time)
        perform_insert(["Sudden", drift_info_time], self.metric)

    def _get_end_time(self, target):
        """
        Get the end time of the command execution based on the specified target metric
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
    def _check_cpu_utilization(target):
        """
        Check if the current CPU utilization reaches the target value
        """
        cpu_utilization = get_current_cpu_utilization()
        return cpu_utilization >= float(target)

    @staticmethod
    def _check_memory_utilization(target):
        """
        Check if the current memory utilization reaches the target value
        """
        mem_utilization = get_current_memory_utilization()
        return mem_utilization >= float(target)

    @staticmethod
    def _check_processes_utilization(target):
        """
        Check if the current number of processes reaches the target value
        """
        processes_count = get_current_processes_num()
        return processes_count >= float(target)
