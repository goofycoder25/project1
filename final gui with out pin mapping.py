import tkinter as tk
from tkinter import ttk
import threading
import time

# =============================================================
# LAUNCHER SCREEN
# =============================================================

class Launcher:
    def __init__(self, root):
        self.root = root
        self.root.title("HMI Launcher")
        self.root.geometry("800x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#0d0d1a")

        tk.Label(
            self.root, text="SELECT PANEL",
            font=("Arial", 28, "bold"),
            bg="#0d0d1a", fg="white"
        ).pack(pady=(100, 50))

        btn_frame = tk.Frame(self.root, bg="#0d0d1a")
        btn_frame.pack()

        tk.Button(
            btn_frame, text="PANEL 1",
            font=("Arial", 18, "bold"),
            width=14, height=3,
            bg="#d0d0d0", fg="#000000",
            command=self.launch_panel1
        ).grid(row=0, column=0, padx=30)

        tk.Button(
            btn_frame, text="PANEL 2",
            font=("Arial", 18, "bold"),
            width=14, height=3,
            bg="#d0d0d0", fg="#000000",
            command=self.launch_panel2
        ).grid(row=0, column=1, padx=30)

    def launch_panel1(self):
        self.root.destroy()
        root2 = tk.Tk()
        Panel1(root2)
        root2.mainloop()

    def launch_panel2(self):
        self.root.destroy()
        root2 = tk.Tk()
        Panel2(root2)
        root2.mainloop()

# =============================================================
# PANEL 1 — GUI ONLY
# =============================================================

class Panel1:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel 1 — HMI")
        self.root.geometry("800x480")
        self.root.resizable(False, False)

        self.switch_names = [
            "M/ARM ON",
            "BOMB ARMED",
            "MAN RANGE",
            "AGM PWR"
        ]

        self.input_active = [True] * 4
        self.output_active = [False] * 4

        self.btn0_last_click = 0
        self.btn0_pending = False

        left = ttk.Frame(root, padding=10)
        left.grid(row=0, column=0, sticky="nw")
        right = ttk.Frame(root, padding=10)
        right.grid(row=0, column=1, sticky="ne")

        ttk.Label(right, text="EVENT LOG",
                  font=("Arial", 11, "bold")).pack()
        self.log = tk.Text(right, width=34, height=18)
        self.log.pack()

        btn_frame = ttk.Frame(left)
        btn_frame.grid(row=0, column=0, columnspan=4, pady=10)

        self.buttons = []
        for i in range(4):
            col = tk.Frame(btn_frame)
            col.grid(row=0, column=i, padx=12)

            btn = tk.Button(
                col, text="READY",
                width=10, height=2,
                bg="#00aa00", fg="white",
                font=("Arial", 10, "bold"),
                command=lambda i=i: self.button_pressed(i)
            )
            btn.pack()
            tk.Label(col, text=self.switch_names[i]).pack()
            self.buttons.append(btn)

        led_frame = ttk.Frame(left)
        led_frame.grid(row=2, column=0, columnspan=4, pady=15)
        self.led_widgets = []
        for name in ["AIM", "AGM GBU", "ROCK", "BOMB"]:
            f = ttk.Frame(led_frame)
            f.pack(side="left", padx=10)
            led = tk.Label(f, bg="gray", width=4, height=2)
            led.pack()
            ttk.Label(f, text=name).pack()
            self.led_widgets.append(led)

    def button_pressed(self, idx):
        if idx == 0:
            now = time.time()
            if self.btn0_pending and (now - self.btn0_last_click) <= 2:
                self.btn0_pending = False
                self.toggle_output(idx)
            else:
                self.btn0_last_click = now
                self.btn0_pending = True
                self.log_event("M/ARM ON: click again within 2s")
                self.root.after(2000, self.cancel_btn0)
        else:
            self.toggle_output(idx)

    def cancel_btn0(self):
        if self.btn0_pending:
            self.btn0_pending = False
            self.log_event("M/ARM ON: timeout")

    def toggle_output(self, idx):
        self.output_active[idx] = not self.output_active[idx]
        state = self.output_active[idx]
        self.buttons[idx].config(
            text="ON" if state else "READY",
            bg="#228822" if state else "#00aa00"
        )
        self.log_event(f"{self.switch_names[idx]} {'ON' if state else 'OFF'}")

    def log_event(self, txt):
        self.log.insert("end", txt + "\n")
        self.log.see("end")

# =============================================================
# PANEL 2 — GUI ONLY
# =============================================================
class Panel2(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=8, pady=6)

        # -------- Simulated states --------
        self.grpA = True
        self.grpB = True

        self.power_state = False
        self.arm_state = False
        self.man_range_state = False
        self.agm_state = False
        self.ind_msl_state = False
        self.out_mode = False

        self.unlock_time = 0
        self.emer_unlocked = False

        self.build_ui()

    # =================================================
    # UI
    # =================================================
    def build_ui(self):
        BTN_W, BTN_H = 12, 2

        # ---------- TOP ----------
        top = ttk.Frame(self)
        top.pack(fill="x")

        # WPN REL DELAY
        wpn = ttk.Frame(top)
        wpn.pack(side="left", padx=10)

        ttk.Label(wpn, text="WPN REL DELAY",
                  font=("Arial",10,"bold")).pack()

        row = ttk.Frame(wpn)
        row.pack()

        lbls = ttk.Frame(row)
        lbls.pack(side="left")
        for t in ["5", "0", "3"]:
            ttk.Label(lbls, text=t).pack(pady=10)

        self.wpn_slider = tk.Scale(
            row, from_=2, to=0,
            orient="vertical",
            length=110,
            showvalue=False,
            command=self.wpn_change
        )
        self.wpn_slider.set(1)
        self.wpn_slider.pack(side="left")

        # Buttons
        self.power_btn = tk.Button(top, text="GND",
                                   width=BTN_W, height=BTN_H,
                                   command=self.toggle_power)
        self.arm_btn = tk.Button(top, text="TAIL",
                                 width=BTN_W, height=BTN_H,
                                 command=self.toggle_arm)
        self.man_btn = tk.Button(top, text="MAN RANGE",
                                 width=BTN_W+2, height=BTN_H,
                                 command=self.toggle_man_range)

        for b in [self.power_btn, self.arm_btn, self.man_btn]:
            b.pack(side="left", padx=6)

        # ---------- MID ----------
        mid = ttk.Frame(self)
        mid.pack(fill="x", pady=8)

        self.agm_btn = tk.Button(mid, text="AGM PWR",
                                 width=BTN_W, height=BTN_H,
                                 command=self.toggle_agm)
        self.btn73 = tk.Button(mid, text="73 COOL",
                               width=BTN_W, height=BTN_H,
                               command=self.toggle_73)
        self.btn27 = tk.Button(mid, text="27T COOL",
                               width=BTN_W, height=BTN_H,
                               command=self.toggle_27)
        self.ind_btn = tk.Button(mid, text="IND MSL MODE",
                                 width=BTN_W+2, height=BTN_H,
                                 command=self.toggle_ind)

        for b in [self.agm_btn, self.btn73, self.btn27, self.ind_btn]:
            b.pack(side="left", padx=6)

        # OUTPUT MODE
        self.out_btn = tk.Button(self, text="SAFE",
                                 width=BTN_W, height=BTN_H,
                                 command=self.toggle_out)
        self.out_btn.pack(pady=4)

        # ---------- BOTTOM ----------
        bottom = ttk.Frame(self)
        bottom.pack(fill="both", expand=True)

        # LEDs
        leds = ttk.Frame(bottom)
        leds.pack(side="left", expand=True)

        self.led_widgets = []
        for name in ["AIM","AGM GBU","ROCK","BOMB"]:
            f = ttk.Frame(leds)
            f.pack(side="left", padx=10)
            led = tk.Label(f, bg="gray", width=4, height=2)
            led.pack()
            ttk.Label(f, text=name).pack()
            self.led_widgets.append(led)

        # EMERGENCY SLIDER
        emer = ttk.Frame(bottom)
        emer.pack(side="right", padx=12)

        ttk.Label(emer, text="EMER LAUNCH").pack()

        self.middle_slider = tk.Scale(
            emer, from_=2, to=0,
            orient="vertical",
            length=160,
            showvalue=False,
            command=self.emer_move
        )
        self.middle_slider.set(1)
        self.middle_slider.pack()
        self.middle_slider.bind("<Button-1>", self.emer_unlock)

        ttk.Label(emer, text="EMER JETT").pack()

    # =================================================
    # LOGIC (SIMULATED)
    # =================================================
    def wpn_change(self, v):
        pass  # purely visual now

    def toggle_power(self):
        self.power_state = not self.power_state
        self.power_btn.config(text="AIR" if self.power_state else "GND")

    def toggle_arm(self):
        self.arm_state = not self.arm_state
        self.arm_btn.config(text="FWD" if self.arm_state else "TAIL")

    def toggle_man_range(self):
        self.man_range_state = not self.man_range_state
        self.man_btn.config(bg="#228822" if self.man_range_state else "#555555")

    def toggle_agm(self):
        self.agm_state = not self.agm_state
        self.agm_btn.config(bg="#228822" if self.agm_state else "#555555")

    def toggle_73(self):
        self.btn73.config(bg="#228822" if self.btn73["bg"] != "#228822" else "#555555")

    def toggle_27(self):
        self.btn27.config(bg="#228822" if self.btn27["bg"] != "#228822" else "#555555")

    def toggle_ind(self):
        self.ind_msl_state = not self.ind_msl_state
        self.ind_btn.config(bg="#228822" if self.ind_msl_state else "#555555")

    def toggle_out(self):
        self.out_mode = not self.out_mode
        self.out_btn.config(text="ARMED" if self.out_mode else "SAFE")

    # -------- Emergency --------
    def emer_unlock(self, event):
        now = time.time()
        if now - self.unlock_time <= 2:
            self.emer_unlocked = True
        self.unlock_time = now

    def emer_move(self, v):
        v = int(v)
        if v == 1 or not self.emer_unlocked:
            self.middle_slider.set(1)
            return
        self.emer_unlocked = False
        self.after(600, lambda: self.middle_slider.set(1))

# =============================================================
# MAIN
# =============================================================

root = tk.Tk()
Launcher(root)
root.mainloop()