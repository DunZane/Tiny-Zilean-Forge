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
        """
        Generate the command for the incremental script.
        This function is used to generate the command for the incremental script.
        It retrieves the currently available memory and generates a new memory load based on this information.
        The function calculates the average memory load for each transition
        based on the total load and the number of transitions.
        If the average load is zero, it sets the average load to 10 to avoid potential errors.
        It determines the command set for the incremental script, including the memory load for each transition.
        :param drift_params (dict): A dictionary containing drift parameters such as type, duration, and shape.
        :return:
            list: A list containing the generated commands for the incremental script.
            int: The duration of each transition.
            int: The total memory load for the incremental script.
        """
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
        """
        Generate sub-drift commands.
        This function generates sub-drift commands based on the number of events provided.
        It randomly selects between "Blip" and "Recurrent" types of events for each sub-drift.
        :param num_events (int): The number of sub-drift events to generate.
        :return:
            list: A list containing the generated sub-drift commands.
            list: A list containing the types of events for each sub-drift.
        """
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
        """
        Generate commands for Sudden type drift.
        This function generates commands for the Sudden type drift.
        It calculates the memory load based on the available processes and the configured scale.
        :return:
            list: A list containing the generated commands for the Sudden type drift.
            None: None (duration is not applicable for Sudden type drift).
            int: The total memory load for the Sudden type drift.
        """
        available_process = get_available_processes_num()
        upper = int(available_process * self.sudden_load_scale['higher'])
        lower = int(available_process * self.sudden_load_scale['lower'])
        fork_num = str(random.randint(lower, upper))
        command = self._cmd_prefix.copy()
        command.extend([fork_num])
        return [command], None, fork_num

    def _generate_blip_script(self, timeout, mode=None):
        """
        Generate commands for Blip type drift.
        This function generates commands for the Blip type drift.
        It calculates the memory load based on the available processes and the configured scale.
        :param timeout (int): The timeout duration for the Blip type drift.
        :param mode (str): The mode of the drift, either 'sub' for sub-drift or None for main drift.
        :return:
            list: A list containing the generated commands for the Blip type drift.
            None: None (duration is not applicable for Blip type drift).
            int: The total memory load for the Blip type drift.
        """
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
        """
        Generate commands for Recurrent type drift.
        This function generates commands for the Recurrent type drift.
        It calculates the memory load based on the available processes and the configured scale.
        :param timeout (int): The timeout duration for the Recurrent type drift.
        :param mode (str): The mode of the drift, either 'sub' for sub-drift or None for main drift.
        :return:
            list: A list containing the generated commands for the Recurrent type drift.
            None: None (duration is not applicable for Recurrent type drift).
            int: The total memory load for the Recurrent type drift.
        """
        available_processes_num = get_available_processes_num()
        if mode is None:
            upper = int(available_processes_num * self.recurrent_load_scale['higher'])
            lower = int(available_processes_num * self.recurrent_load_scale['lower'])
        else:
            upper = int(available_processes_num * self.recurrent_load_scale['higher']) + 40
