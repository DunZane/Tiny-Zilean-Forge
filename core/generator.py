import random

import yaml

with open('config/generator_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

drift_gen = config['settings']['drift_gen']


class DriftGenerator:
    def __init__(self):
        self._drift_types = drift_gen['drift_category']
        self._drift_modes = drift_gen['drift_mode']
        self.increment_amount = drift_gen['incremental'][0]
        self.gradual_amount = drift_gen['gradual'][0]
        self.each_incremental_duration = drift_gen['incremental'][1]

    def generate_drift_parameters(self):
        """
        生成漂移参数。该函数根据随机选择的漂移类型和漂移模式生成相应的漂移参数。
        在生成过程中，可以根据需要添加其他漂移参数。
        :return:
        """
        # 随机选择一种漂移类型
        drift_type = self._generate_random_drift_type()

        # 根据随机选择的漂移类型确定持续时间
        drift_duration, drift_shape = self._generate_drift_duration(drift_type)

        # 随机选择漂移mode
        drift_mode = self._generate_drift_mode()

        # 其他漂移参数的生成逻辑可以在这里添加
        drift_parameters = {
            "type": drift_type,
            "duration": drift_duration,
            "shape": drift_shape,
            "mode": drift_mode,
            # 添加其他漂移参数
        }
        return drift_parameters

    def _generate_random_drift_type(self):
        return random.choice(self._drift_types)

    def _generate_drift_duration(self, drift_type):
        """
        生成漂移持续时间和形状信息。根据不同的漂移类型，生成相应的漂移持续时间和形状信息。
        对于"Blip"和"Recurrent"类型，持续时间是在预先配置的范围内随机选择的。
        对于"Incremental"和"Gradual"类型，持续时间通过调用相关辅助函数进行处理。
        对于"Sudden"类型，漂移没有指定的持续时间。
        :param drift_type: 漂移类型，可以是"Sudden", "Blip", "Recurrent", "Incremental", 或 "Gradual"。
        :return: Union[float, tuple]
        """
        if drift_type == "Sudden":
            # 针对Sudden其结束时间由新分布上的漂移事件来结束
            duration = -1  # -1表示不会指定结束时间
            shape = None

        elif drift_type == "Blip":
            # 针对Blip其持续的时间为1～15s
            blip_scale = drift_gen['blip'][0]
            blip_sec = random.uniform(blip_scale['duration_lower_bound_seconds'],
                                      blip_scale['duration_higher_bound_seconds'])
            duration = blip_sec
            shape = None

        elif drift_type == "Recurrent":
            # 针对Recurrent其持续时间为25～60s
            recurrent_scale = drift_gen['recurrent'][0]
            recurrent_min = random.uniform(recurrent_scale['duration_lower_bound_seconds'],
                                           recurrent_scale['duration_higher_bound_seconds'])
            duration = recurrent_min
            shape = None

        elif drift_type == "Incremental":
            # 针对Incremental其结束时间由新分布上的漂移事件来结束
            shape = self._process_increment_duration()
            duration = -1  # -1表示不会指定结束时间

        elif drift_type == "Gradual":
            # 针对Gradual其结束时间由新分布上的漂移事件来结束
            shape = self._process_gradual_duration()
            duration = -1  # -1表示不会指定结束时间

        else:
            raise ValueError("Unknown drift type")
        return duration, shape

    def _generate_drift_mode(self):
        drift_modes = self._drift_modes
        return random.choice(drift_modes)

    def _process_increment_duration(self):
        """
        该函数用于生成增量持续时间的序列。根据预先配置的区间，随机生成递增的序列长度和每次增量的持续时间。
        :return: 包含递增序列长度和每次增量的持续时间的列表。返回值形式为 [recurrent_sequence_length, each_duration]

        """
        recurrent_sequence_length = random.randint(self.increment_amount['amount_lower_bound'],
                                                   self.increment_amount['amount_higher_bound'])
        each_duration = random.uniform(self.each_incremental_duration['time_fragment_lower_seconds'],
                                       self.each_incremental_duration['time_fragment_higher_seconds'])
        return [recurrent_sequence_length, each_duration]

    def _process_gradual_duration(self):
        """
        处理渐进式漂移的持续时间
        :return: 一个包含递增和递减序列的列表
        """
        gradual_sequence_length = random.randint(self.gradual_amount['time_fragment_lower_seconds'],
                                                 self.gradual_amount['time_fragment_higher_seconds'])
        # 生成逐渐增加的数列
        increasing_sequence = [i for i in range(1, gradual_sequence_length + 1)]
        # 生成逐渐减少的数列
        decreasing_sequence = [i for i in range(gradual_sequence_length, 0, -1)]
        return [increasing_sequence, decreasing_sequence]
