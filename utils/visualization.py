import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime


class Visualization:
    def __init__(self, pkl_path, csv_path):
        self.pkl_path = pkl_path
        self.csv_path = csv_path

    def read_csv_file(self):
        # Read CSV file and sort by '_time'
        drift_data = pd.read_csv(self.csv_path)
        drift_data.sort_values(by='_time', inplace=True)
        return drift_data

    def read_pkl_file(self):
        # Read pickle file with label data
        with open(self.pkl_path, 'rb') as file:
            label_data = pickle.load(file)
        return label_data

    def convert_to_rfc3339(self, label_data):
        # Convert label data time to RFC3339 format
        rfc3339_data = []
        for item in label_data:
            event_type, time_range = item[0], item[1]
            start_time = time_range[0] - datetime.timedelta(hours=8)
            end_time = time_range[1] - datetime.timedelta(hours=8)
            start_time, end_time = start_time.isoformat(), end_time.isoformat()
            rfc3339_data.append([event_type, (start_time, end_time)])
        return rfc3339_data

    def visualize_chunk(self, chunk_data, label_data, chunk_index):
        # Visualize a chunk of data with labels
        colors = {'Sudden': 'blue', 'Blip': 'yellow', 'Recurrent': 'red', 'Incremental': 'green', 'Gradual': 'pink'}

        plt.figure(figsize=(50, 6))
        plt.plot(chunk_data['_time'], chunk_data['_value'], label='_value')

        for label, (start_time, end_time) in label_data:
            start_index = chunk_data[chunk_data['_time'] >= start_time].index
            end_index = chunk_data[chunk_data['_time'] <= end_time].index
            if not start_index.empty and not end_index.empty:
                start_index, end_index = start_index[0], end_index[-1]
                plt.axvspan(chunk_data.at[start_index, '_time'], chunk_data.at[end_index, '_time'],
                            alpha=0.2, label=label, facecolor=colors.get(label, 'gray'))

        plt.xticks([])
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.title(f'Visualization of Data with Labels (Chunk {chunk_index + 1})')
        custom_legend = [plt.Line2D([0], [0], color=colors[label], lw=4, label=label) for label in colors]
        plt.legend(handles=custom_legend, loc='upper right')
        plt.show()

    def visual(self):
        # Read data and preprocess labels
        label_data = self.read_pkl_file()
        drift_data = self.read_csv_file()
        label_data = self.convert_to_rfc3339(label_data)

        # Split data into chunks
        time_chunks = np.array_split(drift_data['_time'], len(drift_data) // 500)

        # Visualize each chunk
        for i, time_chunk in enumerate(time_chunks):
            chunk_data = drift_data[
                (drift_data['_time'] >= time_chunk.iloc[0]) & (drift_data['_time'] <= time_chunk.iloc[-1])]
            self.visualize_chunk(chunk_data, label_data, i + 1)

    def count_drift_num(self):
        # Count the number of drifts in the label data
        drift_data = self.read_pkl_file()
        return len(drift_data)


if __name__ == '__main__':
    # Example usage
    v = Visualization('../storage/cpu_2023-10-23_13-59-29_to_2023-10-24_00-55-54.pkl',
                      '../data/2023-11-17_08_09_influxdb_data.csv')
    v.visual()
