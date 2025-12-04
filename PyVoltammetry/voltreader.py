from datetime import datetime
import pandas as pd
import re
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
pd.options.mode.chained_assignment = None


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
                    date = re.match(r'(\w{3})[\w.]?\s+(\d{1,2}),\s+(\d{4})\s+(\d{2}):(\d{2}):(\d{2})', line)
                    datetuple = date.groups()
                    datestr = (f'{datetuple[0]}. {datetuple[1]}, {datetuple[2]}   '
                               f'{datetuple[3]}:{datetuple[4]}:{datetuple[5]}')
                    self.date = datetime.strptime(datestr, '%b. %d, %Y   %H:%M:%S')

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

        if self.scandir == 'N':
            index_df = self.voltdata[self.voltdata['Potential'] == self.initvolt]
            numcycles = len(index_df)
            indexes = index_df.index
            for i in range(numcycles):
                if i < numcycles - 1:
                    cycledata = self.voltdata.iloc[indexes[i]:indexes[i + 1], :]
                    cycles.append(cycledata)
                else:
                    cycledata = self.voltdata.iloc[indexes[i]:, :]
                    cycles.append(cycledata)
            return cycles
        else:
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

    def smooth_data(self, cycle_number: int, window_length: int=7, polyorder: int=2) -> pd.DataFrame:
        """
        :param cycle_number: Select nth cycle for smoothing.
        :param window_length: Longitud de la ventana de suavisado. Debe ser un número impar
        :param polyorder: Orden del polinomio utilizado para el ajuste.
        :return: Un DataFrame con los datos suavizados.
        """

        try:
            if window_length % 2 == 0 or window_length <= 1:
                raise ValueError('window_length debe ser un número impar mayor que 1.')
            selected_cycle = self.get_cycles()[cycle_number]

            # Aplicar el filtro de Savitzky-Golay
            smooth_current = savgol_filter(selected_cycle['Current'], window_length, polyorder)
            selected_cycle.loc[:, 'Smoothed Current'] = smooth_current
            return selected_cycle
        except Exception as e:
            print(f'Error smoothing data: {e}')
            return None


if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='Extract voltammetry cycles')
    # parser.add_argument('file', type=str, help='Path to voltammetry file')
    # parser.add_argument('--nth', default=-1, type=int, help='Number of cycle to extract')
    # args = parser.parse_args()
    #
    # file = args.file
    # nth = args.nth

    v = Voltammogram('cv l1(-400a125) 200 mvs.txt')
    smoothed = v.smooth_data(1, window_length=7, polyorder=2)
    print(smoothed)
    plt.plot(smoothed['Potential'], smoothed['Smoothed Current'])
    plt.xlabel('Potential (V)')
    plt.ylabel('Current (A)')
    plt.show()
    # cycle = v.get_cycles()[nth]
    # basename = os.path.splitext(os.path.split(file)[1])[0]
    # cycle.to_csv(f'{basename}_origin.csv', index=None)
