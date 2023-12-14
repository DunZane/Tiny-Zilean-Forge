import random

import psutil
import yaml

from core.toolkit.tools import get_current_mem_percent, get_available_memory

with open('config/mem_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

shell_gen = config['settings']['shell_gen']


class MemCmdGenerator:
    def __init__(self):
        self._script_prefix = shell_gen['command_prefix']
        self.sudden_load_scale = shell_gen['sudden_mem_variation_range_percentage'][0]
        self.blip_load_scale = shell_gen['blip_mem_variation_range_percentage'][0]
        self.recurrent_load_scale = shell_gen['recurrent_mem_variation_range_percentage'][0]
        self.incremental_load_scale = shell_gen['incremental_mem_variation_range_percentage'][0]
        self.gradual_load_scale = shell_gen['gradual_mem_variation_range_percentage'][0]

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

    def _generate_sudden_script(self):
        """
        Generate the command for the sudden script.
        This function is used to generate the command for the sudden script.
        It retrieves the currently available memory and generates a new memory load based on this information.
        The sudden load is determined within a specified range, taking the available memory into account.
        For Sudden scripts, no timeout is needed as it continues to generate new drifts on a stable distribution.
        :return:
            list: A list containing the generated command for the sudden script.
            None: This function does not require a specific timeout.
            str: The memory load for the sudden script.
        """
        available_mem = get_available_memory()
        load = str(random.uniform(available_mem * self.sudden_load_scale['lower'],
                                  available_mem * self.sudden_load_scale['higher']))
        command = self._script_prefix.copy()
        command.extend(["--vm-bytes", load + "M"])
        current_mem_percent = get_current_mem_percent()
        return [command], None, current_mem_percent

    def generate_sub_script(self, num_events):
        events = [random.choice(["Blip", "Recurrent"]) for _ in range(num_events)]
        cmds = []
        for event in events:
            available_mem = get_available_memory()
            load = str(random.uniform(available_mem/2,available_mem))
            timeout = random.uniform(15, 40) if event == "Blip" else random.uniform(120, 180)
            if event == "Blip":
                cmd, _, _ = self._generate_blip_script(timeout, load)
            else:
                cmd, _, _ = self._generate_recurrent_script(timeout, load)
            cmds.append(cmd[0])
        return cmds, events

    def _generate_blip_script(self, timeout, load=None):
        """
        Generate the command for the blip script.
        This function is used to generate the command for the blip script. If the load is not provided,
        it generates a random memory load within the specified range based on the available memory.
        If the load is provided, it checks if the provided load is a string; if not, it converts it to a string.
        The function generates a command for the blip script, including the memory load and the timeout value.
        :param timeout (int): The timeout value for the blip script.
        :param load (int or str or None): The memory load for the blip script.
        :return:
            list: A list containing the generated command for the blip script.
            None: This function does not have a specific return duration.
            str: The memory load for the blip script.
        """
        if load is None:
            available_mem = get_available_memory()
            load = str(random.uniform(available_mem * self.blip_load_scale['lower'],
                                      available_mem * self.blip_load_scale['higher']))
        else:
            if type(load) is not str:
                load = str(load)
        command = self._script_prefix.copy()
        command.extend(["--vm-bytes", load + "M", "--timeout", str(timeout)])
        current_mem_percent = get_current_mem_percent()
        return [command], None, current_mem_percent

    def _generate_recurrent_script(self, timeout, load=None):
        """
        Generate the command for the recurrent script.
        This function is used to generate the command for the recurrent script. If the load is not provided,
        it generates a random memory load within a specified range based on the available memory.
        If the load is provided, it checks if the provided load is a string; if not, it converts it to a string.
        It generates a command for the recurrent script, including the memory load and the timeout value.
        :param timeout (int): The timeout value for the recurrent script.
        :param load (int or str or None): The memory load for the recurrent script.
        :return:
            list: A list containing the generated command for the recurrent script.
            None: This function does not have a specific return duration.
            str: The memory load for the recurrent script.
        """
        if load is None:
            available_mem = get_available_memory()
            load = str(random.uniform(available_mem * self.recurrent_load_scale['lower'],
                                      available_mem * self.recurrent_load_scale['higher']))
        else:
            if type(load) is not str:
                load = str(load)
        command = self._script_prefix.copy()
        command.extend(["--vm-bytes", load + "M", "--timeout", str(timeout)])
        current_mem_percent = get_current_mem_percent()
        return [command], None, current_mem_percent

    def _generate_incremental_script(self, shape):
        """
        Generate the command for the incremental script.
        This function is used to generate the command for the incremental script. It retrieves the
        currently available memory and generates a new memory load based on this information.
        The function calculates the average memory load for each transition based on the total
        load and the number of transitions.If the average load is zero,
        it sets the average load to 10 to avoid potential errors.
        It determines the command set for the incremental script, including the memory load for each transition.
        :param shape (tuple): A tuple containing the number of transitions and their durations.
        :return:
            list: A list containing the generated commands for the incremental script.
            int: The duration of each transition.
            int: The total memory load for the incremental script.
        """
        available_mem = get_available_memory()
        load = random.uniform(available_mem * self.incremental_load_scale['lower'],
                              available_mem * self.incremental_load_scale['higher'])
        num_transition = shape[0]
        duration_transition = shape[1]
        average_load = int(load / num_transition)
        if average_load != 0:
            average_load = str(average_load)
        else:
            average_load = str(10)
        commands, sleep_time = [], []
        for i in range(num_transition):
            command = self._script_prefix.copy()
            command.extend(["--vm-bytes", average_load + "M"])
            commands.append(command)
        current_mem_percent = get_current_mem_percent()
        return commands, duration_transition, current_mem_percent

    def _generate_gradual_script(self, shape):
        """
        Generate the command for the incremental script.
        This function is used to generate the command for the incremental script.
        It retrieves the currently available memory and generates a new memory load based on this information.
        The function calculates the average memory load for each transition
        based on the total load and the number of transitions.
        If the average load is zero, it sets the average load to 10 to avoid potential errors.
        It determines the command set for the incremental script, including the memory load for each transition.
        :param shape (tuple): A tuple containing the number of transitions and their durations.
        :return:
            list: A list containing the generated commands for the incremental script.
            int: The duration of each transition.
            int: The total memory load for the incremental script.
        """
        available_mem = get_available_memory()
        load = str(random.uniform(available_mem * self.gradual_load_scale['lower'],
                                  available_mem * self.gradual_load_scale['higher']))
        scale = random.choice(shell_gen['time_scale'])
        timeout_list = [i * scale for i in shape[0]]
        sleep_list = [i * scale for i in shape[1]]
        commands = []
        for i in range(len(timeout_list)):
            timeout = str(timeout_list[i])
            command = self._script_prefix.copy()
            command.extend(["--vm-bytes", load + "M"])
            if i != len(timeout_list) - 1:
                command.extend(["--timeout", timeout + "s"])
                commands.append(command)
            else:
                commands.append(command)
        current_mem_percent = get_current_mem_percent()
        return commands, sleep_list, current_mem_percent


