import tkinter as tk
from tkinter import ttk, scrolledtext
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import pygame
import speech_recognition as sr
import os
import webbrowser
import pyautogui
import subprocess
from threading import Thread
from time import sleep
from datetime import datetime

# Инициализация звука
pygame.mixer.init()

class LinkLabel(tk.Label):
    def __init__(self, master, text, url, **kwargs):
        super().__init__(master, text=text, fg="blue", cursor="hand2", **kwargs)
        self.url = url
        self.bind("<Button-1>", self.open_link)
        self.bind("<Enter>", lambda e: self.config(font=("Segoe UI", 10, "underline")))
        self.bind("<Leave>", lambda e: self.config(font=("Segoe UI", 10)))

    def open_link(self, event):
        webbrowser.open(self.url)

class VoiceAssistant(ttkb.Window):
    def __init__(self):
        super().__init__(themename="morph")
        self.title("Голосовой ассистент")
        self.geometry("1000x750")

        # Стилизация
        style = ttkb.Style()
        style.configure("Title.TLabel", font=("Helvetica", 16, "bold"))
        style.configure("Command.TLabel", font=("Segoe UI", 10))
        style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"))

        # Основные фреймы
        self.main_frame = ttkb.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

        # Левая панель (навигация + логи)
        self.left_frame = ttkb.Frame(self.main_frame)
        self.left_frame.pack(side=LEFT, fill=Y, padx=(0, 10))

        # Панель навигации
        self.nav_frame = ttkb.Labelframe(self.left_frame, text="Меню", bootstyle=INFO)
        self.nav_frame.pack(fill=X, pady=(0, 10))

        nav_buttons = [
            ("Основное", self.show_main),
            ("Команды", self.show_commands),
            ("Помощь", self.show_help)
        ]

        for text, command in nav_buttons:
            ttkb.Button(self.nav_frame, text=text, bootstyle=OUTLINE, 
                       width=15, command=command).pack(pady=3, padx=5, fill=X)

        # Панель логов
        self.log_frame = ttkb.Labelframe(self.left_frame, text="Журнал", bootstyle=SECONDARY)
        self.log_frame.pack(fill=BOTH, expand=True)

        self.log_area = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, width=40, height=20)
        self.log_area.pack(fill=BOTH, expand=True)
        self.log_area.insert(tk.END, f"{datetime.now().strftime('%H:%M')} Система инициализирована\n")
        self.log_area.configure(state='disabled')

        # Правая панель (основной контент)
        self.right_frame = ttkb.Frame(self.main_frame)
        self.right_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        self.commands_list = [
            "🎤 привет - приветствие",
            "🌐 открой браузер - открыть Google",
            "🎵 открой яндекс - Яндекс.Музыка",
            "❌ закрой браузер - закрыть Chrome",
            "📝 открой блокнот - открыть Блокнот",
            "📌 закрой блокнот - закрыть Блокнот",
            "🔼 прокрути вверх - скролл вверх",
            "🔽 прокрути вниз - скролл вниз",
            "⏎ нажми enter - нажать Enter",
            "⏻ выключи компьютер - выключить ПК",
            "💻 работа - открыть VS Code",
            "🚪 стоп - выключить ассистента"
        ]

        self.content_frames = {
            "main": self.create_main_content(),
            "commands": self.create_commands_content(),
            "settings": self.create_settings_content(),
            "help": self.create_help_content()
        }

        self.show_main()

        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
        except OSError:
            self.microphone = None
            self.add_log("Микрофон не найден")

        self.is_running = False

        self.command_actions = {
            "привет": lambda: (self.add_log("Приветствие"), self.play_sound("sounds/o-privet.mp3")),
            "открой браузер": lambda: webbrowser.open("https://google.com"),
            "открой яндекс": lambda: webbrowser.open("https://music.yandex.ru"),
            "закрой браузер": lambda: os.system("taskkill /f /im chrome.exe"),
            "открой блокнот": lambda: subprocess.Popen("notepad.exe"),
            "закрой блокнот": lambda: os.system("taskkill /f /im notepad.exe"),
            "прокрути вверх": lambda: pyautogui.scroll(100),
            "прокрути вниз": lambda: pyautogui.scroll(-100),
            "нажми enter": lambda: pyautogui.press("enter"),
            "выключи компьютер": lambda: (self.play_sound("sounds/-do-svidaniya.mp3"), os.system("shutdown /s /t 1")),
            "работа": lambda: subprocess.Popen("code"),
            "стоп": self.stop_assistant
        }

    def create_main_content(self):
        frame = ttkb.Frame(self.right_frame)
        status_frame = ttkb.Labelframe(frame, text="Статус", bootstyle=SUCCESS)
        status_frame.pack(fill=X)
        self.status_var = tk.StringVar(value="🟢 Готов к работе")
        status_label = ttkb.Label(status_frame, textvariable=self.status_var, style="Status.TLabel")
        status_label.pack(pady=5)

        control_frame = ttkb.Frame(frame)
        control_frame.pack(fill=X, pady=10)

        self.start_btn = ttkb.Button(control_frame, text="🎙️ Запустить", bootstyle=SUCCESS, command=self.start_assistant)
        self.stop_btn = ttkb.Button(control_frame, text="⏹ Остановить", bootstyle=DANGER, command=self.stop_assistant)

        self.start_btn.pack(side=LEFT, padx=5)
        self.stop_btn.pack(side=LEFT, padx=5)
        ttkb.Button(control_frame, text="❌ Выход", bootstyle=DARK, command=self.destroy).pack(side=RIGHT, padx=5)

        return frame

    def create_commands_content(self):
        frame = ttkb.Frame(self.right_frame)
        commands_frame = ttkb.Labelframe(frame, text="Доступные команды", bootstyle=PRIMARY)
        commands_frame.pack(fill=BOTH, expand=True, pady=(10, 0))
        for cmd in self.commands_list:
            ttkb.Label(commands_frame, text=cmd, style="Command.TLabel").pack(anchor='w', padx=10, pady=2)
        return frame

    def create_settings_content(self):
        frame = ttkb.Frame(self.right_frame)
        ttkb.Label(frame, text="Настройки ассистента", style="Title.TLabel").pack(pady=10)
        ttkb.Label(frame, text="Раздел настроек в разработке", style="Command.TLabel").pack(pady=20)
        return frame

    def create_help_content(self):
        frame = ttkb.Frame(self.right_frame)
        ttkb.Label(frame, text="Помощь и поддержка", style="Title.TLabel").pack(pady=10)
        github_frame = ttkb.Frame(frame)
        github_frame.pack(fill=X, pady=5)
        ttkb.Label(github_frame, text="Developer: ", style="Command.TLabel").pack(side=LEFT)
        LinkLabel(github_frame, text="https://github.com/tebenkov-prog", url="https://github.com/tebenkov-prog").pack(side=LEFT)
        telegram_frame = ttkb.Frame(frame)
        telegram_frame.pack(fill=X, pady=5)
        ttkb.Label(telegram_frame, text="Поддержка: ", style="Command.TLabel").pack(side=LEFT)
        LinkLabel(telegram_frame, text="https://t.me/tebenkov_games", url="https://t.me/tebenkov_games").pack(side=LEFT)
        ttkb.Label(frame, text="\nПо всем вопросам и предложениям обращайтесь по указанным ссылкам.", style="Command.TLabel").pack(pady=10)
        return frame

    def show_main(self):
        self.hide_all_content()
        self.content_frames["main"].pack(fill=BOTH, expand=True)

    def show_commands(self):
        self.hide_all_content()
        self.content_frames["commands"].pack(fill=BOTH, expand=True)

    def show_settings(self):
        self.hide_all_content()
        self.content_frames["settings"].pack(fill=BOTH, expand=True)

    def show_help(self):
        self.hide_all_content()
        self.content_frames["help"].pack(fill=BOTH, expand=True)

    def hide_all_content(self):
        for frame in self.content_frames.values():
            frame.pack_forget()

    def add_log(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, f"{datetime.now().strftime('%H:%M')} {message}\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')
        self.update()

    def play_sound(self, filename):
        try:
            sound = pygame.mixer.Sound(filename)
            sound.play()
            sleep(0.3)
        except Exception as e:
            self.add_log(f"Ошибка звука: {e}")

    def listen_command(self):
        if not self.microphone:
            self.add_log("Нет микрофона для записи")
            return ""

        with self.microphone as source:
            self.status_var.set("🔵 Слушаю...")
            self.add_log("Ожидание команды")
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)

        try:
            command = self.recognizer.recognize_google(audio, language="ru-RU").lower()
            self.add_log(f"Распознано: {command}")
            self.status_var.set(f"🎤 {command[:20]}...")
            return command
        except sr.UnknownValueError:
            self.add_log("Не распознано")
            self.status_var.set("🟠 Не распознано")
            return ""
        except sr.RequestError:
            self.add_log("Ошибка сервиса")
            self.status_var.set("🔴 Ошибка сервиса")
            return ""

    def execute_command(self, command):
        for cmd, action in self.command_actions.items():
            if cmd in command:
                self.add_log(f"Выполняю: {cmd}")
                self.status_var.set(f"⚡ {cmd}...")
                try:
                    action()
                    self.add_log("Успешно выполнено")
                    self.status_var.set("🟢 Готов")
                except Exception as e:
                    self.add_log(f"Ошибка при выполнении: {e}")
                    self.status_var.set("🔴 Ошибка выполнения")
                return True
        self.add_log("Неизвестная команда")
        self.status_var.set("🟠 Неизвестная команда")
        return False

    def assistant_loop(self):
        self.play_sound("sounds/welcome.mp3")
        self.add_log("Ассистент активирован")
        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        while self.is_running:
            command = self.listen_command()
            if command:
                if "стоп" in command:
                    self.play_sound("sounds/goodbye.mp3")
                    self.add_log("Завершение работы")
                    self.status_var.set("🔴 Выключение...")
                    sleep(2)
                    self.stop_assistant()
                    break
                self.execute_command(command)

    def start_assistant(self):
        if not self.is_running:
            self.thread = Thread(target=self.assistant_loop, daemon=True)
            self.thread.start()

    def stop_assistant(self):
        self.is_running = False
        self.status_var.set("🟢 Готов к работе")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

if __name__ == "__main__":
    app = VoiceAssistant()
    app.mainloop()