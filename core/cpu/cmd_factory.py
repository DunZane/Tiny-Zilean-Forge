import random
import yaml
from core.toolkit.tools import get_current_cpu_available

with open('config/cpu_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

shell_gen = config['settings']['shell_gen']


class CpuCmdGenerator:
    def __init__(self):
        self._script_prefix = shell_gen['command_prefix']
        self._sudden_load_scale = shell_gen['sudden_cpu_variation_range_percentage'][0]
        self._blip_load_scale = shell_gen['blip_cpu_variation_range_percentage'][0]
        self._recurrent_load_scale = shell_gen['recurrent_cpu_variation_range_percentage'][0]
        self._incremental_load_scale = shell_gen['incremental_cpu_variation_range_percentage'][0]
        self._gradual_load_scale = shell_gen['gradual_cpu_variation_range_percentage'][0]
        self._time_scale = shell_gen['time_scale']

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

    def generate_sub_script(self, num_events):
        events = [random.choice(["Blip", "Recurrent"]) for _ in range(num_events)]
        cmds = []
        # 获取当前可用的load
        available_cpu = get_current_cpu_available()
        for event in events:
            timeout = random.uniform(30, 40) if event == "Blip" else random.uniform(120, 180)

            if event == "Blip":
                load = str(random.uniform((available_cpu * 4) / 5, available_cpu))
                cmd, _, _ = self._generate_blip_script(timeout, load)
            else:
                load = str(random.uniform((available_cpu * 4) / 5, available_cpu))
                cmd, _, _ = self._generate_recurrent_script(timeout, load)
            cmds.append(cmd[0])
        return cmds, events

    def _generate_sudden_script(self):
        """
        Generate the command for sudden drift.
        This function is used to generate the command for sudden drift.
        The load is within the range of 3 to 5 times the machine's current state.
        It is not recommended to exceed 5 times.
        :return:
            list: A list containing the generated command for sudden drift.
            None: This function does not have any duration.
            str: The load value for the sudden drift.
        """
        load = str(random.uniform(self._sudden_load_scale['lower'],
                                  self._sudden_load_scale['higher']))
        command = self._script_prefix.copy()
        command.extend(["--cpu-load", load])
        return [command], None, load

    def _generate_blip_script(self, timeout, load=None):
        """
        Generate the command for the blip drift.
        This function is used to generate the command for the blip drift.
        If the load is not provided, a random CPU load within the specified range is chosen.
        It is important to note that the timeout for blip should not be too large,
        and is generally recommended to have a relatively small duration paired with a higher CPU configuration value.
        :param timeout（int）: The timeout value for the blip drift
        :param load (int or None): The CPU load for the blip drift.
        :return:
            list: A list containing the generated command for the blip drift.
            None: This function does not have any duration.
            str: The load value for the blip drift.
        """
        if load is None:
            load = str(random.uniform(self._blip_load_scale['lower'],
                                      self._blip_load_scale['higher']))
        else:
            load = str(load)
        command = self._script_prefix.copy()
        command.extend(["--cpu-load", load, "--timeout", str(timeout)])
        return [command], None, load

    def _generate_recurrent_script(self, timeout, load=None):
        """
        Generate the command for the recurrent script.
        This function is used to generate the command for the recurrent script.
        If the load is not provided, a random CPU load within the specified range is chosen.
        It is important to note that the timeout for recurrent should not be too small,
        and is generally recommended to have a relatively moderate duration paired
        with an appropriate CPU configuration value.
        :param timeout (int): The timeout value for the recurrent script.
        :param load (int or None): The CPU load for the recurrent script.
        :return:
            list: A list containing the generated command for the recurrent script.
            None: This function does not have any specific return duration.
            str: The load value for the recurrent script.
        """
        # 生成随机的CPU负载
        if load is None:
            load = str(random.uniform(self._recurrent_load_scale['lower'],
                                      self._recurrent_load_scale['higher']))
        else:
            load = str(load)
        command = self._script_prefix.copy()
        command.extend(["--cpu-load", load, "--timeout", str(timeout)])
        return [command], None, load

    def _generate_incremental_script(self, shape):
        """
        Generate the command for the incremental script.
        This function is used to generate the command for the incremental script.
        A random CPU load within the specified range is chosen for each incremental step.
        The backoff value is randomly chosen between 1000 and 5000.
        The function retrieves drift parameters such as the number of transitions and their durations.
        The average CPU load for each transition is calculated based on the total load and the number of transitions.
        It saves all the generated commands for the incremental script.
        :param shape (tuple): A tuple containing the number of transitions and their durations.
        :return:
            list: A list containing the generated commands for the incremental script.
            int: The duration of each transition.
            int: The total CPU load for the incremental script.
        """
        load = random.uniform(self._incremental_load_scale['lower'],
                              self._incremental_load_scale['higher'])
        backoff = str(random.randint(1000, 5000))
        num_transition = shape[0]
        duration_transition = shape[1]
        average_load = str(load / num_transition)
        commands, sleep_time = [], []
        for i in range(num_transition):
            command = self._script_prefix.copy()
            command.extend(["--cpu-load", average_load, "--backoff", backoff])
            commands.append(command)
        return commands, duration_transition, load

    def _generate_gradual_script(self, shape):
        """
        Generate the command for the gradual script.
        This function is used to generate the command for the gradual script.
        A random CPU load within the specified range is chosen, with the range parameters retrieved from the configuration file.
        The function handles different stages of duration and sleep times based on the input shape.
        It generates a list of commands for the gradual script, each with its own CPU load and timeout configuration.
        :param (tuple): A tuple containing the duration for each stage and the sleep times.
        :return:
            list: A list containing the generated commands for the gradual script.
            list: A list containing the sleep times for each stage.
            str: The CPU load for the gradual script.
        """
        load = str(random.randint(self._gradual_load_scale['lower'],
                                  self._gradual_load_scale['higher']))

        duration_list = shape[0]
        time_scale = random.choice(self._time_scale)
        sleep_time_list = [i * time_scale for i in shape[1]]
        commands = []
        for i in range(len(duration_list)):
            duration = str(duration_list[i])
            command = self._script_prefix.copy()
            command.extend(["--cpu-load", load])
            if i != len(duration_list) - 1:
                command.extend(["--timeout", duration + "m"])
                commands.append(command)
            else:
                commands.append(command)
        return commands, sleep_time_list, load
