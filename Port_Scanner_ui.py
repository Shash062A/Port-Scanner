import customtkinter as ctk
import threading
import socket
from datetime import datetime
from queue import Queue
import json
import csv
from tkinter import filedialog
import time
import winsound   # For sound (Windows only)

# ================== ORIGINAL LOGIC (UNCHANGED) ==================

COMMON_SERVICES = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    8080: "HTTP-ALT"
}

MAX_THREADS = 100

class PortScanner:
    def __init__(self, ui):
        self.ui = ui
        self.open_ports = {}
        self.lock = threading.Lock()
        self.scanned_ports = 0
        self.running = False
        self.port_queue = Queue()

    def banner_grab(self, sock):
        try:
            sock.send(b"HELLO\r\n")
            return sock.recv(1024).decode(errors="ignore").strip()
        except:
            return "No banner"

    def check_ports(self, ip, port, delay):
        if not self.running:
            return

        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(delay)
            result = sock.connect_ex((ip, port))

            if result == 0:
                service = COMMON_SERVICES.get(port, "Unknown")
                banner = self.banner_grab(sock)

                with self.lock:
                    self.open_ports[port] = \
                        f"Open | Service: {service} | Banner: {banner}"

                    self.ui.add_result(
                        f"OPEN PORT {port} → {self.open_ports[port]}"
                    )

        except:
            pass
        finally:
            if sock:
                sock.close()

        with self.lock:
            self.scanned_ports += 1
            self.ui.update_progress()

    def worker(self, ip, delay):
        while not self.port_queue.empty() and self.running:
            port = self.port_queue.get()
            self.check_ports(ip, port, delay)
            self.port_queue.task_done()

    def start_scan(self, host, start, end, delay):
        self.running = True
        self.scanned_ports = 0
        self.open_ports.clear()
        self.ui.scan_start_time = time.time()

        try:
            host_ip = socket.gethostbyname(host)
        except:
            self.ui.add_result("Host not found!")
            return

        total_ports = end - start
        self.ui.set_total_ports(total_ports)
        self.ui.add_result(f"Scanning {host} ({host_ip})")

        for port in range(start, end):
            self.port_queue.put(port)

        threads = []
        for _ in range(MAX_THREADS):
            t = threading.Thread(target=self.worker,
                                 args=(host_ip, delay))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.running = False
        self.ui.add_result("Scan Completed.")

    def stop_scan(self):
        self.running = False

# ================== LOGIN SCREEN ==================

class Login(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Authentication Required")
        self.geometry("400x300")

        # Dark Green Hacker Theme
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#02150b")  # Main background

        # Container Frame
        self.container = ctk.CTkFrame(self,
                                      fg_color="#000000",
                                      corner_radius=15)
        self.container.pack(expand=True, fill="both", padx=20, pady=20)

        # Header
        ctk.CTkLabel(
            self.container,
            text="🔐 Authentication Panel",
            font=("Consolas", 18, "bold"),
            text_color="#1f8f4e"
        ).pack(pady=20)

        # Username Entry
        self.user = ctk.CTkEntry(
            self.container,
            placeholder_text="Username",
            fg_color="#02150b",
            text_color="#1f8f4e",
            border_color="#14532d"
        )
        self.user.pack(pady=10, padx=40)

        # Password Entry
        self.passw = ctk.CTkEntry(
            self.container,
            placeholder_text="Password",
            show="*",
            fg_color="#02150b",
            text_color="#1f8f4e",
            border_color="#14532d"
        )
        self.passw.pack(pady=10, padx=40)

        # Login Button
        ctk.CTkButton(
            self.container,
            text="Login",
            fg_color="#14532d",
            hover_color="#1f8f4e",
            text_color="black",
            font=("Consolas", 14, "bold"),
            command=self.check_login
        ).pack(pady=20)

    def check_login(self):
        if self.user.get() == "Shash062A" and self.passw.get() == "062A":
            self.destroy()
            app = App()
            app.mainloop()
        else:
            winsound.Beep(400, 200)

# ================== MAIN APP ==================

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("System Port Scanner For Penetration")
        self.geometry("1100x700")
        self.configure(fg_color="#011f14")

        ctk.set_appearance_mode("dark")

        self.total_ports = 1
        self.scan_start_time = 0
        self.scanner = PortScanner(self)

        self.build_layout()
        self.update_clock()
        self.animate_dots()

    def build_layout(self):

        self.sidebar = ctk.CTkFrame(self, width=250, fg_color="#000000")
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(self.sidebar,
                     text="SYSTEM PORTS",
                     font=("Consolas", 16, "bold"),justify="center",
                     text_color="#1f8f4e").pack(pady=10)

        self.host = ctk.CTkEntry(self.sidebar, placeholder_text="Host",fg_color="#02150b",
            text_color="#1f8f4e",border_color="#14532d",justify="center")
        self.host.pack(pady=5, padx=10)

        self.start_port = ctk.CTkEntry(self.sidebar, placeholder_text="Start Port",fg_color="#02150b",
            text_color="#1f8f4e",border_color="#14532d",justify="center")
        self.start_port.pack(pady=5, padx=10)

        self.end_port = ctk.CTkEntry(self.sidebar, placeholder_text="End Port",fg_color="#02150b",
            text_color="#1f8f4e",border_color="#14532d",justify="center")
        self.end_port.pack(pady=5, padx=10)

        self.delay = ctk.CTkEntry(self.sidebar, placeholder_text="Delay {0.001}",fg_color="#02150b",
            text_color="#1f8f4e",border_color="#14532d",justify="center")
        self.delay.pack(pady=5, padx=10)

        ctk.CTkButton(self.sidebar, text="Start Scan",
                      fg_color="#14532d",
                      command=self.start_scan_thread).pack(pady=8)

        ctk.CTkButton(self.sidebar, text="Stop Scan",
                      fg_color="#3f0000",
                      command=self.stop_scan).pack(pady=5)

        ctk.CTkButton(self.sidebar, text="Fullscreen Toggle",
                      fg_color="#123524",
                      command=self.toggle_fullscreen).pack(pady=5)

        self.main_area = ctk.CTkFrame(self, fg_color="#02150b")
        self.main_area.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.clock_label = ctk.CTkLabel(self.main_area,
                                        text="",
                                        font=("Consolas", 14),
                                        text_color="#1f8f4e")
        self.clock_label.pack()

        self.scan_time_label = ctk.CTkLabel(self.main_area,
                                            text="Scan Time: 0s",
                                            text_color="#1f8f4e")
        self.scan_time_label.pack()

        self.port_counter = ctk.CTkLabel(self.main_area,
                                         text="Open Ports: 0",
                                         text_color="#1f8f4e")
        self.port_counter.pack()

        self.progress = ctk.CTkProgressBar(self.main_area,
                                           progress_color="#14532d")
        self.progress.pack(fill="x", padx=20, pady=10)

        self.textbox = ctk.CTkTextbox(self.main_area,
                                      fg_color="#000000",
                                      text_color="#1f8f4e",
                                      font=("Consolas", 12))
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)

    # ---------------- FEATURES ----------------

    def toggle_fullscreen(self):
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

    def update_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.clock_label.configure(text=f"Live Time: {now}")
        self.after(1000, self.update_clock)

        if self.scanner.running:
            elapsed = int(time.time() - self.scan_start_time)
            self.scan_time_label.configure(text=f"Scan Time: {elapsed}s")

    def animate_dots(self):
        if self.scanner.running:
            self.textbox.insert("end", ".")
            self.textbox.see("end")
        self.after(500, self.animate_dots)

    def start_scan_thread(self):
        winsound.Beep(800, 150)
        host = self.host.get() or "localhost"
        start = int(self.start_port.get() or 0)
        end = int(self.end_port.get() or 1000)
        delay = float(self.delay.get() or 0.001)

        threading.Thread(
            target=self.scanner.start_scan,
            args=(host, start, end, delay),
            daemon=True
        ).start()

    def stop_scan(self):
        self.scanner.stop_scan()
        winsound.Beep(400, 200)

    def add_result(self, text):

        if "OPEN PORT" in text:
            winsound.Beep(1000, 100)

            # Severity color coding
            if any(p in text for p in ["21", "23", "25"]):
                tag = "high"
                color = "#7f1d1d"
                warning = "⚠ Vulnerable service detected!\n"
                self.textbox.insert("end", warning, "warn")
                self.textbox.tag_config("warn", foreground="#ff4444")
            else:
                tag = "open"
                color = "#1f8f4e"

            self.textbox.insert("end", text + "\n", tag)
            self.textbox.tag_config(tag, foreground=color)

            self.port_counter.configure(
                text=f"Open Ports: {len(self.scanner.open_ports)}"
            )
        else:
            self.textbox.insert("end", text + "\n")

        self.textbox.see("end")

    def set_total_ports(self, total):
        self.total_ports = total
        self.progress.set(0)

    def update_progress(self):
        value = self.scanner.scanned_ports / self.total_ports
        self.progress.set(value)

# ================== RUN ==================

if __name__ == "__main__":
    login = Login()
    login.mainloop()