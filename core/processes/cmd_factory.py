import random

import yaml

from core.toolkit.tools import get_available_processes_num

with open('config/processes_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

shell_gen = config['settings']['shell_gen']


class ProcessesGenerator:
    def __init__(self):
        self._cmd_prefix = shell_gen['command_prefix']
        self.sudden_load_scale = shell_gen['sudden_thread_variation_range_percentage'][0]
        self.blip_load_scale = shell_gen['blip_thread_variation_range_percentage'][0]
        self.recurrent_load_scale = shell_gen['recurrent_thread_variation_range_percentage'][0]
        self.incremental_load_scale = shell_gen['incremental_thread_variation_range_percentage'][0]
        self.gradual_load_scale = shell_gen['gradual_thread_variation_range_percentage'][0]

    def generate_script(self, drift_params):
        drift_type = drift_params['type']
        drift_duration = drift_params['duration']
        drift_shape = drift_params['shape']
        if drift_type == "Sudden":
            return self._generate_sudden_script()
        elif drift_type == "Blip":
            return self._generate_blip_script(drift_duration)
        elif drift_type == "Recurrent":
            return self._generate_recurrent_script(drift_duration)
        elif drift_type == "Incremental":
            return self._generate_incremental_script(drift_shape)
        elif drift_type == "Gradual":
            return self._generate_gradual_script(drift_shape)
        else:
            raise ValueError("Unknown drift type")
        pass

    def generate_sub_script(self, num_events):
        events = [random.choice(["Blip", "Recurrent"]) for _ in range(num_events)]
        cmds = []
        for event in events:
            timeout = random.uniform(15, 40) if event == "Blip" else random.uniform(120, 180)
            if event == "Blip":
                cmd, _, _ = self._generate_blip_script(timeout, 'sub')
            else:
                cmd, _, _ = self._generate_recurrent_script(timeout)
            cmds.append(cmd[0])
        return cmds, events
        pass

    def _generate_sudden_script(self):
        available_process = get_available_processes_num()
        upper = int(available_process * self.sudden_load_scale['higher'])
        lower = int(available_process * self.sudden_load_scale['lower'])
        fork_num = str(random.randint(lower, upper))
        command = self._cmd_prefix.copy()
        command.extend([fork_num])
        return [command], None, fork_num

    def _generate_blip_script(self, timeout, mode=None):
        available_processes_num = get_available_processes_num()
        if mode is None:
            upper = int(available_processes_num * self.blip_load_scale['higher'])
        else:
            upper = int(available_processes_num * self.blip_load_scale['higher']) + 20
        fork_num = str(random.randint(5, upper))
        command = self._cmd_prefix.copy()
        command.extend([fork_num, "--timeout", str(timeout)])
        return [command], None, fork_num

    def _generate_recurrent_script(self, timeout, mode=None):
        available_processes_num = get_available_processes_num()
        if mode is None:
            upper = int(available_processes_num * self.recurrent_load_scale['higher'])
            lower = int(available_processes_num * self.recurrent_load_scale['lower'])
        else:
            upper = int(available_processes_num * self.recurrent_load_scale['higher']) + 40
            lower = int(available_processes_num * self.recurrent_load_scale['lower']) + 20
        fork_num = str(random.randint(lower, upper))
        command = self._cmd_prefix.copy()
        command.extend([fork_num, "--timeout", str(timeout)])
        return [command], None, fork_num

    def _generate_incremental_script(self, shape):
        available_processes_num = get_available_processes_num()
        upper = int(available_processes_num * self.incremental_load_scale['higher'])
        lower = int(available_processes_num * self.incremental_load_scale['lower'])
        fork_num = random.randint(lower, upper)
        num_transition = shape[0]
        duration_transition = shape[1]
        average_load = int(fork_num / num_transition)
        if average_load != 0:
            average_load = str(average_load)
        else:
            average_load = str(1)
        commands, sleep_time = [], []
        for i in range(num_transition):
            command = self._cmd_prefix.copy()
            command.extend([average_load])
            commands.append(command)
        return commands, duration_transition, fork_num

    def _generate_gradual_script(self, shape):
        available_processes_num = get_available_processes_num()
        upper = int(available_processes_num * self.gradual_load_scale['higher'])
        lower = int(available_processes_num * self.gradual_load_scale['lower'])
        fork_num = str(random.randint(lower, upper))
        scale = random.choice(shell_gen['time_scale'])
        timeout_list = [i * scale for i in shape[0]]
        sleep_list = [i * scale for i in shape[1]]
        commands = []
        for i in range(len(timeout_list)):
            timeout = str(timeout_list[i])
            command = self._cmd_prefix.copy()
            command.extend([fork_num])
            if i != len(timeout_list) - 1:
                command.extend(["--timeout", timeout + "s"])
                commands.append(command)
            else:
                commands.append(command)
        return commands, sleep_list, fork_num
