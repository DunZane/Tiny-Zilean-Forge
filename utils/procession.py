import os
import pickle
from datetime import datetime, timedelta
import pandas as pd


class DataProcessor:
    def __init__(self, label_data_path, drift_data_path):
        self.label_data_path = label_data_path
        self.drift_data_path = drift_data_path
        self.event_types = {'Sudden': 1, 'Blip': 2, 'Recurrent': 3, 'Incremental': 4, 'Gradual': 5}
        self.resampled_data = None

    def process_data(self):
        # Load label and drift data
        label_data = self.load_label_data()
        drift_data = self.load_drift_data()

        # Process data
        annotated_data = self.convert_to_annotated_data(label_data, drift_data)
        length_list = self.process_continuous(annotated_data)
        df = self.save_as_csv(annotated_data, length_list)
        self.extract_segments(df)

    def load_label_data(self):
        # Load label data from CSV
        label_data = pd.read_csv(self.label_data_path)
        return label_data

    def load_drift_data(self):
        # Load and preprocess drift data
        drift_data = pd.read_csv(self.drift_data_path)
        drift_data['_time'] = pd.to_datetime(drift_data['_time'])
        drift_data.sort_values(by='_time', inplace=True)
        drift_data.set_index('_time', inplace=True)
        drift_data = drift_data.resample('1S').asfreq().interpolate(method='linear')
        return drift_data

    @staticmethod
    def convert_to_rfc3339(label_data):
        # Convert label data time to RFC3339 format
        rfc3339_data = []
        for item in label_data.iterrows():
            event_type = item[1][1]
            start_time = datetime.strptime(item[1][2], '%d/%m/%Y %H:%M:%S') - timedelta(hours=8)
            end_time = datetime.strptime(item[1][3], '%d/%m/%Y %H:%M:%S') - timedelta(hours=8)
            start_time, end_time = start_time.isoformat(), end_time.isoformat()
            rfc3339_data.append([event_type, (start_time, end_time)])
        return rfc3339_data

    def convert_to_annotated_data(self, label_data, drift_data):
        # Convert data to annotated format
        annotated_data, temp = [], []
        rfc3339_data = self.convert_to_rfc3339(label_data)
        timestep = self.create_standard_timestep()
        self.resampled_data = drift_data.reindex(timestep, method='ffill')

        for timestamp, row in self.resampled_data.iterrows():
            value = row['_value']
            found = False
            for label in rfc3339_data:
                drift_type, (drift_start, drift_end) = label
                if drift_start <= timestamp <= drift_end:
                    temp.append([timestamp, value, self.event_types[drift_type]])
                    found = True
                    break
            if not found:
                annotated_data.append([timestamp, value, 0])
            else:
                annotated_data.extend(temp)
                temp = []
        return annotated_data

    def create_standard_timestep(self):
        # Create standard timestep based on label file name
        file_name = os.path.basename(self.label_data_path).strip(".csv")
        start_time = f"{file_name.split('_')[1]} {file_name.split('_')[2].replace('-', ':')}"
        end_time = f"{file_name.split('_')[4]} {file_name.split('_')[5].replace('-', ':')}"
        start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8)
        end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S') - timedelta(hours=8)
        time_columns = pd.date_range(start=start_time, end=end_time, freq='10S')
        time_columns = [timestep.strftime('%Y-%m-%dT%H:%M:%SZ') for timestep in time_columns]
        return time_columns

    @staticmethod
    def process_continuous(data):
        # Process continuous data and return a list of lengths
        length = 0
        result = []
        for _, _, val in data:
            if val != 0:
                length += 1
            else:
                if length > 0:
                    result.extend([length] * length)
                    length = 0
                result.append(0)
        if length > 0:
            result.extend([length] * length)
        return result

    def save_as_csv(self, annotated_data, length_data):
        # Save annotated data as CSV and return DataFrame
        df = pd.DataFrame(annotated_data, columns=['timestamp', 'value', 'category_label'])
        df['drift_label'] = length_data
        new_file_name = os.path.basename(self.label_data_path).replace('project', 'cpu').replace('.pkl', '.csv')
        new_file_path = f"processed/{new_file_name}"
        df.to_csv(new_file_path, index=False)
        return df

    def save_as_pkl(self, drift_segments):
        # Save drift segments as pickle file
        new_file_name = os.path.basename(self.label_data_path).replace('project', 'cpu').strip(".csv")
        new_file_path = f'processed/standard_drift_index_{new_file_name}.pkl'
        with open(new_file_path, 'wb') as file:
            pickle.dump(drift_segments, file)
        return new_file_path

    def extract_segments(self, resampled_data):
        # Extract segments from resampled data and save as pickle
        segments = []
        drift_label_list = resampled_data['drift_label'].to_list()
        start_index, index = 0, 0
        while index < len(drift_label_list):
            if drift_label_list[index] != 0:
                start_index = index
                end_index = start_index + drift_label_list[index]
                segments.append([start_index, end_index])
                index = end_index
            else:
                index = index + 1
        self.save_as_pkl(segments)
        return segments


if __name__ == '__main__':
    # Example usage
    p = DataProcessor(
        '../storage/mem_2023-11-03_00-00-00_to_2023-12-14_09-00-00.csv',
        '../data/2023-12-14_10_20_influxdb_data.csv')
    p.process_data()
