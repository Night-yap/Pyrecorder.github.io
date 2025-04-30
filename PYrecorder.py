import sys
import sounddevice as sd
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QComboBox, QLabel, QMessageBox, QProgressBar, QInputDialog)
from PyQt6.QtCore import QTimer
import wave
from datetime import datetime
import lameenc

class AudioRecorder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("シンプル録音ソフト")
        self.setGeometry(100, 100, 400, 250)

        self.audio_format, ok = QInputDialog.getItem(
            self, "保存形式の選択", "保存形式を選んでください:", ["WAV", "MP3"], 0, False)
        if not ok:
            sys.exit()

        self.sample_rate = 44100
        self.recording_data = []
        self.is_recording = False

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        self.mic_label = QLabel("マイクを選択してください:")
        layout.addWidget(self.mic_label)

        self.mic_combo = QComboBox()
        self.update_mic_list()
        layout.addWidget(self.mic_combo)

        self.volume_label = QLabel("音量レベル:")
        layout.addWidget(self.volume_label)

        self.volume_bar = QProgressBar()
        self.volume_bar.setRange(0, 100)
        layout.addWidget(self.volume_bar)

        self.record_button = QPushButton("録音開始")
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)

        self.volume_timer = QTimer()
        self.volume_timer.timeout.connect(self.update_volume)
        self.volume_timer.setInterval(50)

    def update_mic_list(self):
        self.mic_combo.clear()
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                self.mic_combo.addItem(device['name'], i)

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        try:
            self.device_id = self.mic_combo.currentData()
            self.recording_data = []
            self.is_recording = True
            self.record_button.setText("録音停止")

            def callback(indata, frames, time, status):
                if status:
                    print(status)
                self.recording_data.append(indata.copy())
                self.current_volume = np.abs(indata).mean() * 100

            self.stream = sd.InputStream(
                device=self.device_id,
                channels=1,
                samplerate=self.sample_rate,
                callback=callback
            )
            self.stream.start()
            self.volume_timer.start()

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"録音開始に失敗しました:\n{str(e)}")
            self.record_button.setText("録音開始")

    def update_volume(self):
        if hasattr(self, 'current_volume'):
            self.volume_bar.setValue(min(100, int(self.current_volume * 2)))

    def stop_recording(self):
        self.stream.stop()
        self.stream.close()
        self.volume_timer.stop()
        self.volume_bar.setValue(0)
        self.record_button.setText("録音開始")
        self.is_recording = False

        if self.recording_data:
            self.save_recording()

    def save_recording(self):
        try:
            audio_data = np.concatenate(self.recording_data, axis=0)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if self.audio_format == "WAV":
                filename = f"recording_{timestamp}.wav"
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())

            elif self.audio_format == "MP3":
                filename = f"recording_{timestamp}.mp3"
                encoder = lameenc.Encoder()
                encoder.set_bit_rate(128)
                encoder.set_in_sample_rate(self.sample_rate)
                encoder.set_channels(1)
                encoder.set_quality(2)
                mp3_data = encoder.encode((audio_data * 32767).astype(np.int16).tobytes())
                mp3_data += encoder.flush()
                with open(filename, 'wb') as f:
                    f.write(mp3_data)

            QMessageBox.information(self, "保存完了", f"保存しました: {filename}")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"保存に失敗しました:\n{str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    recorder = AudioRecorder()
    recorder.show()
    sys.exit(app.exec())
