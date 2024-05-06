import random
import yaml
from typing import Dict, Union, List, Tuple

class DriftGenerator:
    def __init__(self, config_path: str):
        """
        Initialize DriftGenerator with configurations.
        :param config_path: Path to the configuration YAML file.
        """
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

        self._drift_gen = config['settings']['drift_gen']
        self._drift_types = self._drift_gen['drift_category']
        self._drift_modes = self._drift_gen['drift_mode']
        self.increment_amount = self._drift_gen['incremental'][0]
        self.gradual_amount = self._drift_gen['gradual'][0]
        self.each_incremental_duration = self._drift_gen['incremental'][1]

    def generate_drift_parameters(self) -> Dict[str, Union[str, float, Tuple]]:
        """
        Generate drift parameters based on random drift type and mode.
        :return: Dictionary containing drift parameters.
        """
        drift_type = self._generate_random_drift_type()
        drift_duration, drift_shape = self._generate_drift_duration(drift_type)
        drift_mode = self._generate_drift_mode()

        drift_parameters = {
            "type": drift_type,
            "duration": drift_duration,
            "shape": drift_shape,
            "mode": drift_mode,
            # Additional drift parameters can be added here
        }
        return drift_parameters

    def _generate_random_drift_type(self) -> str:
        """
        Randomly select a drift type from the available types.
        :return: Selected drift type.
        """
        return random.choice(self._drift_types)

    def _generate_drift_duration(self, drift_type: str) -> Tuple[Union[float, int], Union[None, List[int]]]:
        """
        Generate drift duration and shape based on drift type.
        :param drift_type: Type of drift.
        :return: Tuple containing duration and shape information.
        """
        if drift_type == "Sudden":
            # For Sudden type, no specific duration is specified
            duration = -1
            shape = None
        elif drift_type in ["Blip", "Recurrent"]:
            # For Blip and Recurrent types, duration is within a range
            duration = self._generate_bounded_duration(drift_type)
            shape = None
        elif drift_type in ["Incremental", "Gradual"]:
            # For Incremental and Gradual types, duration is handled separately
            shape = self._process_increment_or_gradual_duration(drift_type)
            duration = -1
        else:
            raise ValueError("Unknown drift type")
        return duration, shape

    def _generate_bounded_duration(self, drift_type: str) -> float:
        """
        Generate a random duration within the specified bounds for Blip and Recurrent types.
        :param drift_type: Type of drift.
        :return: Random duration.
        """
        scale = self._drift_gen[drift_type.lower()][0]
        return random.uniform(scale['duration_lower_bound_seconds'], scale['duration_higher_bound_seconds'])

    def _generate_drift_mode(self) -> str:
        """
        Randomly select a drift mode from the available modes.
        :return: Selected drift mode.
        """
        return random.choice(self._drift_modes)

    def _process_increment_or_gradual_duration(self, drift_type: str) -> List[int]:
        """
        Generate a sequence of durations for Incremental and Gradual drift types.
        :param drift_type: Type of drift.
        :return: List containing duration sequences.
        """
        amount_config = self.increment_amount if drift_type == "Incremental" else self.gradual_amount
        sequence_length = random.randint(amount_config['time_fragment_lower_seconds'],
                                         amount_config['time_fragment_higher_seconds'])
        increasing_sequence = list(range(1, sequence_length + 1))
        decreasing_sequence = list(range(sequence_length, 0, -1))
        return [increasing_sequence, decreasing_sequence]

# Example usage:
if __name__ == "__main__":
    generator = DriftGenerator('config/generator_config.yaml')
    parameters = generator.generate_drift_parameters()
    print(parameters)
