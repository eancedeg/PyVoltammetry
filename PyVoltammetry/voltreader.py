from datetime import datetime
import pandas as pd
import argparse
import os


class Voltammogram(object):
    def __init__(self, file):
        self.file = file
        self.date = ''
        self.technique = ''
        self.voltdata = []

        line = 'Data'
        data_section = False
        header = True
        with open(self.file) as volt:
            while line:
                if header:
                    # Date
                    line = volt.readline().strip()
                    self.date = datetime.strptime(line, '%b. %d, %Y   %H:%M:%S')

                    # Technique
                    self.technique = volt.readline().strip()

                    for i in range(6):
                        volt.readline()

                    # Voltammogram parameters
                    self.initvolt = float(volt.readline().split('=')[1])
                    self.highvolt = float(volt.readline().split('=')[1])
                    self.lowvolt = float(volt.readline().split('=')[1])
                    self.scandir = volt.readline().split('=')[1].strip()
                    self.scanrate = float(volt.readline().split('=')[1])
                    self.segments = int(volt.readline().split('=')[1])
                    self.sample_interval = float(volt.readline().split('=')[1])

                    while not data_section:
                        line = volt.readline()
                        if 'Potential/V, Current/A' in line:
                            line = volt.readline()
                            header = False
                            data_section = True
                if data_section:
                    line = volt.readline()
                    if line:
                        linedata = [[float(v.strip()), float(i.strip())] for v, i in [line.split(',')]]
                        self.voltdata.append(linedata[0])
        self.voltdata = pd.DataFrame(self.voltdata, columns=['Potential', 'Current'])

    def get_cycles(self):
        cycles = []
        index_df = self.voltdata[self.voltdata['Potential'] == self.lowvolt]

        if self.initvolt == self.lowvolt:
            index_df = index_df.drop(0)

        indexes = index_df.index
        numcycles = len(indexes.tolist()) + 1

        for i in range(numcycles):
            if i == 0:
                cycledata = self.voltdata.iloc[:indexes[i], :]
                cycles.append(cycledata)
            elif i == numcycles - 1:
                cycledata = self.voltdata.iloc[indexes[i - 1]:, :]
                cycles.append(cycledata)
            else:
                cycledata = self.voltdata.iloc[indexes[i - 1]: indexes[i], :]
                cycles.append(cycledata)
        return cycles


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract voltammetry cycles')
    parser.add_argument('file', type=str, help='Path to voltammetry file')
    parser.add_argument('--nth', default=-1, type=int, help='Number of cycle to extract')
    args = parser.parse_args()

    file = args.file
    nth = args.nth

    v = Voltammogram(file)
    cycle = v.get_cycles()[nth]
    basename = os.path.splitext(os.path.split(file)[1])[0]
    cycle.to_csv(f'{basename}_origin.csv', index=None)