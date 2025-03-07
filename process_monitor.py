import tkinter as tk
from tkinter import ttk
import psutil
import time
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from collections import deque
import os

class ProcessMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Монитор процессов Windows")
        self.root.geometry("1000x600")
        self.root.minsize(800, 500)
        
        # Настройка стиля
        style = ttk.Style()
        style.theme_use('clam')
        
        # Создание основного фрейма
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Создание верхней панели с информацией о системе
        self.system_frame = ttk.LabelFrame(main_frame, text="Информация о системе")
        self.system_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Метки для системной информации
        self.cpu_label = ttk.Label(self.system_frame, text="Загрузка CPU: 0%")
        self.cpu_label.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        
        self.memory_label = ttk.Label(self.system_frame, text="Использование памяти: 0%")
        self.memory_label.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        
        self.disk_label = ttk.Label(self.system_frame, text="Использование диска: 0%")
        self.disk_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        
        self.network_label = ttk.Label(self.system_frame, text="Сеть: 0 Кб/с")
        self.network_label.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Создание панели с графиками
        self.graph_frame = ttk.LabelFrame(main_frame, text="Графики использования ресурсов")
        self.graph_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Создание фигуры для графиков
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Инициализация данных для графиков
        self.time_data = deque(maxlen=60)
        self.cpu_data = deque(maxlen=60)
        self.memory_data = deque(maxlen=60)
        
        # Настройка графиков
        self.ax1.set_title('Загрузка CPU (%)')
        self.ax1.set_ylim(0, 100)
        self.ax1.grid(True)
        self.cpu_line, = self.ax1.plot([], [], 'b-')
        
        self.ax2.set_title('Использование памяти (%)')
        self.ax2.set_ylim(0, 100)
        self.ax2.grid(True)
        self.memory_line, = self.ax2.plot([], [], 'r-')
        
        self.fig.tight_layout()
        
        # Создание таблицы процессов
        self.process_frame = ttk.LabelFrame(main_frame, text="Запущенные процессы")
        self.process_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создание таблицы
        columns = ("PID", "Имя", "CPU %", "Память %", "Память (МБ)", "Статус")
        self.process_tree = ttk.Treeview(self.process_frame, columns=columns, show="headings")
        
        # Настройка заголовков
        for col in columns:
            self.process_tree.heading(col, text=col)
            self.process_tree.column(col, width=100, anchor=tk.CENTER)
        
        # Добавление полосы прокрутки
        scrollbar = ttk.Scrollbar(self.process_frame, orient=tk.VERTICAL, command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.process_tree.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки управления
        self.control_frame = ttk.Frame(main_frame)
        self.control_frame.pack(fill=tk.X, pady=10)
        
        self.refresh_button = ttk.Button(self.control_frame, text="Обновить", command=self.update_data)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        self.sort_cpu_button = ttk.Button(self.control_frame, text="Сортировать по CPU", 
                                         command=lambda: self.sort_processes("CPU %"))
        self.sort_cpu_button.pack(side=tk.LEFT, padx=5)
        
        self.sort_memory_button = ttk.Button(self.control_frame, text="Сортировать по памяти", 
                                           command=lambda: self.sort_processes("Память %"))
        self.sort_memory_button.pack(side=tk.LEFT, padx=5)
        
        # Переменные для хранения данных
        self.processes_data = []
        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_update_time = time.time()
        
        # Запуск обновления данных
        self.update_data()
        
        # Запуск анимации графиков
        self.ani = animation.FuncAnimation(self.fig, self.update_plots, interval=1000)
        
        # Запуск периодического обновления в отдельном потоке
        self.update_thread = threading.Thread(target=self.periodic_update, daemon=True)
        self.update_thread.start()
    
    def update_data(self):
        """Обновление всех данных"""
        self.update_system_info()
        self.update_processes_list()
    
    def update_system_info(self):
        """Обновление информации о системе"""
        # CPU
        cpu_percent = psutil.cpu_percent()
        self.cpu_label.config(text=f"Загрузка CPU: {cpu_percent:.1f}%")
        
        # Память
        memory = psutil.virtual_memory()
        self.memory_label.config(text=f"Использование памяти: {memory.percent:.1f}% ({self.format_bytes(memory.used)}/{self.format_bytes(memory.total)})")
        
        # Диск
        current_time = time.time()
        time_diff = current_time - self.last_update_time
        
        current_disk_io = psutil.disk_io_counters()
        disk_read_speed = (current_disk_io.read_bytes - self.last_disk_io.read_bytes) / time_diff
        disk_write_speed = (current_disk_io.write_bytes - self.last_disk_io.write_bytes) / time_diff
        self.disk_label.config(text=f"Диск: Чтение {self.format_bytes(disk_read_speed)}/с, Запись {self.format_bytes(disk_write_speed)}/с")
        self.last_disk_io = current_disk_io
        
        # Сеть
        current_net_io = psutil.net_io_counters()
        net_sent_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_diff
        net_recv_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_diff
        self.network_label.config(text=f"Сеть: Отправка {self.format_bytes(net_sent_speed)}/с, Получение {self.format_bytes(net_recv_speed)}/с")
        self.last_net_io = current_net_io
        
        self.last_update_time = current_time
        
        # Обновление данных для графиков
        self.time_data.append(len(self.time_data))
        self.cpu_data.append(cpu_percent)
        self.memory_data.append(memory.percent)
    
    def update_processes_list(self):
        """Обновление списка процессов"""
        # Очистка таблицы
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        # Получение списка процессов
        self.processes_data = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                process_info = proc.info
                memory_mb = proc.memory_info().rss / (1024 * 1024)
                self.processes_data.append({
                    'pid': process_info['pid'],
                    'name': process_info['name'],
                    'cpu_percent': process_info['cpu_percent'],
                    'memory_percent': process_info['memory_percent'],
                    'memory_mb': memory_mb,
                    'status': process_info['status']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Сортировка по использованию CPU (по умолчанию)
        self.processes_data.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        # Заполнение таблицы
        for proc in self.processes_data:
            self.process_tree.insert("", tk.END, values=(
                proc['pid'],
                proc['name'],
                f"{proc['cpu_percent']:.1f}",
                f"{proc['memory_percent']:.1f}",
                f"{proc['memory_mb']:.1f}",
                proc['status']
            ))
    
    def sort_processes(self, column):
        """Сортировка процессов по указанному столбцу"""
        if column == "CPU %":
            self.processes_data.sort(key=lambda x: x['cpu_percent'], reverse=True)
        elif column == "Память %":
            self.processes_data.sort(key=lambda x: x['memory_percent'], reverse=True)
        
        # Очистка и заполнение таблицы
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        for proc in self.processes_data:
            self.process_tree.insert("", tk.END, values=(
                proc['pid'],
                proc['name'],
                f"{proc['cpu_percent']:.1f}",
                f"{proc['memory_percent']:.1f}",
                f"{proc['memory_mb']:.1f}",
                proc['status']
            ))
    
    def update_plots(self, frame):
        """Обновление графиков"""
        if len(self.time_data) > 1:
            x_data = list(range(len(self.time_data)))
            self.cpu_line.set_data(x_data, self.cpu_data)
            self.memory_line.set_data(x_data, self.memory_data)
            
            self.ax1.set_xlim(0, len(self.time_data) - 1)
            self.ax2.set_xlim(0, len(self.time_data) - 1)
        
        return self.cpu_line, self.memory_line
    
    def periodic_update(self):
        """Периодическое обновление данных в отдельном потоке"""
        while True:
            time.sleep(2)  # Обновление каждые 2 секунды
            self.root.after(0, self.update_data)
    
    def format_bytes(self, bytes_value):
        """Форматирование байтов в читаемый вид"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} ПБ"

if __name__ == "__main__":
    root = tk.Tk()
    app = ProcessMonitor(root)
    root.mainloop() 