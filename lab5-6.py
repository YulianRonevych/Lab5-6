import tkinter as tk
from tkinter import ttk
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
from datetime import datetime
import os

# Функція для обчислення амплітуди звукових хвиль
def calculate_amplitude(audio_data):
    return np.max(np.abs(audio_data))

# Функція для відображення амплітуди звукових хвиль
def print_amplitude(indata, frames, time, status):
    global recording_started, recorded_frames, output_counter, start_time, total_duration
    amplitude = calculate_amplitude(indata) * 1000
    amplitude_text.delete(1.0, tk.END)
    amplitude_text.insert(tk.END, f"Amplitude: {amplitude:.2f}\n")
    amplitude_text.see(tk.END)

    log_amplitude_change(amplitude)

    if recording_started:
        recorded_frames.append(indata.copy())

    if amplitude > 40 and not recording_started:
        start_recording(indata)
    elif amplitude <= 10 and recording_started:
        stop_recording()

# Функція для логування змін амплітуди
def log_amplitude_change(amplitude):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - Amplitude: {amplitude:.2f}\n"

    with open("logs.txt", "a") as log_file:
        log_file.write(log_entry)

# Функція для початку запису звукових сигналів
def start_recording(indata):
    global recording_started, recorded_frames, output_counter, start_time
    recording_started = True
    start_time = datetime.now()
    print("Recording Started")
    recorded_frames = [indata.copy()]
    update_total_samples_label()

# Функція для завершення запису звукових сигналів
def stop_recording():
    global recording_started, recorded_frames, fs, output_counter, start_time, total_duration
    if recording_started:
        recording_started = False
        print("Recording Stopped")
        if recorded_frames:
            duration = (datetime.now() - start_time).total_seconds()
            if duration >= 0.4:
                output_filename = f"sample{output_counter}.wav"
                output_path = os.path.join("Sample", output_filename)
                frames = np.concatenate(recorded_frames, axis=0)
                wav.write(output_path, fs, frames)
                total_duration += duration
                output_counter += 1
                update_average_duration_label()
            else:
                print(f"Ignored recording with duration {duration} seconds")

# Функція для початку прослуховування звукових сигналів
def start_listening():
    global stream, fs
    selected_device_index = devices_combobox.current()
    if selected_device_index:
        selected_device_info = devices[selected_device_index]
        selected_device_id = selected_device_info['index']
        stream = sd.InputStream(callback=print_amplitude, device=selected_device_id, channels=1, samplerate=fs)
        stream.start()
        start_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
    else:
        print("Please select a device.")

# Функція для завершення прослуховування звукових сигналів
def stop_listening():
    global stream
    if stream:
        stop_recording()
        stream.stop()
        stream.close()
        create_output_folder_and_modify_samples()

    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)

# Функція для оновлення текстової мітки з середньою тривалістю зразків
def update_average_duration_label():
    global output_counter, total_duration
    average_duration = total_duration / output_counter if output_counter > 0 else 0
    average_duration_text.delete(1.0, tk.END)
    average_duration_text.insert(tk.END, f"Average Duration: {average_duration:.2f} seconds")

# Функція для оновлення текстової мітки з загальною кількістю зразків
def update_total_samples_label():
    global output_counter
    total_samples_text.delete(1.0, tk.END)
    total_samples_text.insert(tk.END, f"Total Samples Saved: {output_counter}")

# Функція для створення каталогів та зміни зразків звуків
def create_output_folder_and_modify_samples():
    global total_duration, output_counter

    sample_folder = "Sample"
    if not os.path.exists(sample_folder):
        print(f"'{sample_folder}' folder does not exist.")
        return

    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    max_sample_length = 0
    for i in range(1, output_counter + 1):
        sample_filename = f"sample{i}.wav"
        sample_path = os.path.join(sample_folder, sample_filename)
        if os.path.exists(sample_path):  # Перевірка наявності файлу
            _, sample_data = wav.read(sample_path)
            max_sample_length = max(max_sample_length, len(sample_data))

    for i in range(1, output_counter + 1):
        sample_filename = f"sample{i}.wav"
        sample_path = os.path.join(sample_folder, sample_filename)

        if os.path.exists(sample_path):  # Перевірка наявності файлу
            _, sample_data = wav.read(sample_path)

            if len(sample_data) < max_sample_length:
                padding = np.zeros(max_sample_length - len(sample_data))
                sample_data = np.concatenate((sample_data, padding))

            output_filename = f"output{i}.wav"
            if i+1 == output_counter:
                output_filename = f"Test.wav"
            output_path = os.path.join(output_folder, output_filename)
            wav.write(output_path, fs, sample_data)

root = tk.Tk()
root.title("Microphone Amplitude")

# Інтерфейс
devices = sd.query_devices()
devices_names = [f"{device['name']}" for device in devices]
devices_combobox = ttk.Combobox(root, values=devices_names, state="readonly", font=("Helvetica", 12))
default_device_index = [i for i, device in enumerate(devices) if
                        "Microphone" in device['name'] and device['max_input_channels'] > 0]
devices_combobox.current(default_device_index[0] if default_device_index else 0)
devices_combobox.pack(pady=10)

average_duration_label = tk.Label(root, text="Середня тривалість зразка:", font=("Helvetica", 12))
average_duration_label.pack()

average_duration_text = tk.Text(root, height=1, width=20, font=("Helvetica", 12))
average_duration_text.pack(pady=5, anchor='center', fill='x')

total_samples_label = tk.Label(root, text="Загальна кількість зразків:", font=("Helvetica", 12))
total_samples_label.pack()

total_samples_text = tk.Text(root, height=1, width=20, font=("Helvetica", 12))
total_samples_text.pack(pady=5, anchor='center', fill='x')

start_button = tk.Button(root, text="Почати прослуховування", command=start_listening, font=("Helvetica", 12))
start_button.pack(pady=5)

stop_button = tk.Button(root, text="Зупинити прослуховування", command=stop_listening, state=tk.DISABLED, font=("Helvetica", 12))
stop_button.pack(pady=5)

amplitude_label = tk.Label(root, text="Амплітуда:", font=("Helvetica", 12))
amplitude_label.pack()

amplitude_text = tk.Text(root, height=2, width=20, font=("Helvetica", 12))
amplitude_text.pack(pady=5, anchor='center', fill='x')

#Глобальні змінні для відстеження метрик
recording_started = False
recorded_frames = None
fs = 44100
output_counter = 1
start_time = None
total_duration = 0

if not os.path.exists("Sample"):
    os.makedirs("Sample")

root.mainloop()