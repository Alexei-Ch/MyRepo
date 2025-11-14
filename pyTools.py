import matplotlib.pyplot as plt
from datetime import datetime
import os

class Tools():

    def __init__(self, ):
        
        self.Transforms = {'RES2T': self.Trasform_RES_to_Temp, }

    def Trasform_RES_to_Temp(self, y_data, Rc=0, **kwargs):
        #преобразование сопротивления в температуру
        return [((y-Rc)/100-1)/0.00385 for y in y_data]

    def ParseArguments(self, LaunchArguments=None, ):
        ''' принимает список из аргументов в формате строк
            возвращает словарь с правильными типами данных
            и словарь с аргументами для подключения к прибору'''
        #создаем словарь из аргументов, с которыми была запущена программа
        Arguments = dict(arg.split(':', 1) for arg in LaunchArguments)
        #список имен аргументов, относящихся к установке соединения с прибором
        ConnectNames = ['ConnectionMethod', 'DeviceAddress', 'DevicePort', 'DeviceSerial', ]
        #словарь с аргументами для установки соединения, передается в Device.Initialize()
        ConnectionDetails = {name: Arguments[name] for name in ConnectNames if name in Arguments}
        #словарь для парсинга аргументов
        conversions = {
            #парсим ConfigName, если он словарь (для двухканального TH1992B)
            'ConfigName': lambda x: dict(arg.split(':', 1) for arg in x.split(',')) if ':' in x else x,
            #преобразуем строки в числа
            'MeasTime': float,
            'MeasPoints': int,
            'CanvasPoints': int,
            #формируем списки из имен измеряемых величин
            'DataNames': lambda x: x.split(','),
            'LineNames': lambda x: x.split(','),
            #конвертируем строки в булевые переменные
            'EnablePlot': lambda x: {'true': True, 'false': False}[x.lower()],
            'YTransform': lambda x: {'true': True, 'false': False}[x.lower()],
        }
        #парсим аргументы
        for key, converter in conversions.items():
            if key in Arguments:
                Arguments[key] = converter(Arguments[key])
        return Arguments, ConnectionDetails
    
    def CreateSavePath(self, file, LAN_Path=None, ):
        ''' формирует путь к папке для сохранения данных
            и создает в ней подпапку с текущей датой
            возвращает путь в виде строки '''
        LoggerPath = os.path.dirname(os.path.abspath(file))
        TodayNameDir = '\\' + datetime.now().strftime("%Y_%m_%d") + '\\'
        #сохраняем в хранилище MetroBulk, если оно доступно
        if os.path.exists(LAN_Path):
            SavePath = LAN_Path + TodayNameDir
        #если подключение к MetroBulk отсутствует - сохраняем в местную папку Data
        else:
            SavePath = LoggerPath + '\\Data'+ TodayNameDir
        #создаем папку с текущей датой, если ее нет
        try:
            os.mkdir(SavePath)
        except:
            pass
        return SavePath

    def FormatTime(self, seconds, ):
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d} час {m:02d} мин {s:02d} сек" if h else f"{m:02d} мин {s:02d} сек" if m else f"{s:02d} сек"


class Plotter():

    def __init__(self, y_names, x_label='x', y_label='y', plot_name='Test', pts={}):

        self.pts=pts
        
        #интерактивный режим плота вкл
        plt.ion()
    
        colors = ['b', 'k', 'r', 'm', 'g', 'c',]
        #'linestyle':'solid', 'linewidth':0.3, 'marker':'.', 'markersize':1,
        #line_options = {'c':new_color}
    
        self.lines = {}
        self.xdata, self.ydata = [], {}
        
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.ax.set_title(label=plot_name, fontname='Arial', fontsize=12, )
        self.ax.set_xlabel(xlabel=x_label, fontname='Arial', fontsize=12, )
        self.ax.set_ylabel(ylabel=y_label, fontname='Arial', fontsize=12, )
        if self.pts:
            self.x_step, self.x_pts = self.pts['x_step'], self.pts['x_pts']
            self.ax.set_xlim([0, self.x_step * self.x_pts])
    
        for name in y_names:
            self.lines[name], = self.ax.plot([], [], c=colors[y_names.index(name)], label=name)
            self.ydata[name] = []
    
        plt.show()


    def plot_routine(self, i, x, results, ):

        #добавляем значение x к массиву
        self.xdata.append(x)

        #удаляем "убежавшее" значение x и обновляем лимиты оси
        if self.pts:
            if i+1 > self.x_pts:
                self.xdata = self.xdata[1:]
                xmin, xmax = min(self.xdata), max(self.xdata)
                self.ax.set_xlim(xmin, xmax)

        #итерируем линии
        for name, line in self.lines.items():
            
            #добавляем измеренное значение y в линию
            self.ydata[name].append(results[name])

            #удаляем "убежавшее" значение y
            if self.pts:
                if i+1 > self.x_pts:
                    self.ydata[name] = self.ydata[name][1:]
            
            #записываем списки данных с обновленными значениями в плот
            line.set_ydata(self.ydata[name])
            line.set_xdata(self.xdata)

        #лимиты осей
        self.ax.relim()
        self.ax.autoscale_view()
        #создаем/обновляем легенду
        self.ax.legend(loc='best', fontsize='x-small', markerscale=2.5)
        #перерисовываем плот
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


    def save_figure(self, file_path, ):

        plt.savefig(file_path+'.png')

        