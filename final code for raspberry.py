import tkinter as tk
from tkinter import ttk
import threading
import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("Running in simulation mode (No GPIO)")
    class GPIO:
        BCM = None
        OUT = IN = LOW = HIGH = PUD_DOWN = None
        @staticmethod
        def setmode(x): pass
        @staticmethod
        def setwarnings(x): pass
        @staticmethod
        def setup(a, b, initial=None, pull_up_down=None): pass
        @staticmethod
        def output(a, b): pass
        @staticmethod
        def input(a): return 0
        @staticmethod
        def cleanup(): pass

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# =============================================================
# PANEL 1 — GPIO PIN MAP
# Logical Pin → GPIO (BCM)
# =============================================================
P1_INPUTS = {
    2: 17,   # Pin 11
    3: 27,   # Pin 13
    4: 22,   # Pin 15
    5: 23,   # Pin 16
    6: 24,   # Pin 18
    7: 25,   # Pin 22
}

P1_OUTPUTS = {
    8:  12,  # Pin 32
    9:  6,   # Pin 31
    10: 13,  # Pin 33
    12: 5,   # Pin 29
}

P1_LED_INPUTS = {
    13: 16,  # Pin 36 — Common Enable
    14: 19,  # Pin 35 — LED GND (POWER STATUS)
    15: 20,  # Pin 38 — LED GND (ARM STATUS)
    16: 21,  # Pin 40 — LED GND (NAV STATUS)
    17: 26,  # Pin 37 — LED GND (COMMS STATUS)
}

# =============================================================
# PANEL 2 — GPIO PIN MAP
# Logical Pin → GPIO (BCM)
# =============================================================
P2_INPUTS = {
    4: 22,   # Pin 15 — Enable group A (controls, sliders, btns)
    5: 23,   # Pin 16 — Enable group A
    6: 24,   # Pin 18 — Enable group B (output mode + middle slider)
    7: 25,   # Pin 22 — Enable group B
}

P2_OUTPUTS = {
    9:  12,  # Pin 32 — Execute
    10: 18,  # Pin 12 — Slider UP
    11: 10,  # Pin 19 — Slider DOWN
    12: 6,   # Pin 31 — Output Mode
    13: 15,  # Pin 10 — BTN 5
    14: 2,   # Pin 3  — Power ON
    15: 3,   # Pin 5  — System ARM
    16: 14,  # Pin 8  — BTN 3
    17: 4,   # Pin 7  — BTN 2
    18: 9,   # Pin 21 — Mode C
    19: 11,  # Pin 23 — Mode A
    # BTN 1 shares physical pin with P1 logical 10
    # P2 logical 10 used for slider UP, BTN1 reuses P1 logical 10 GPIO 13 Pin 33
    # We assign a separate logical ref below:
}
# BTN 1 output = same physical as P1 logical 10 = GPIO 13 = Pin 33
P2_BTN1_GPIO = 13

P2_LED_INPUTS = {
    20: 16,  # Pin 36 — Common Enable
    21: 19,  # Pin 35 — LED 1 GND
    22: 20,  # Pin 38 — LED 2 GND
    23: 21,  # Pin 40 — LED 3 GND
    24: 26,  # Pin 37 — LED 4 GND
}

# =============================================================
# GPIO SETUP — done once at startup, reconfigured per panel
# =============================================================

def setup_gpio_panel1():
    for gpio in P1_INPUTS.values():
        GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    for gpio in P1_OUTPUTS.values():
        GPIO.setup(gpio, GPIO.OUT, initial=GPIO.LOW)
    for gpio in P1_LED_INPUTS.values():
        GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def setup_gpio_panel2():
    for gpio in P2_INPUTS.values():
        GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    for gpio in P2_OUTPUTS.values():
        GPIO.setup(gpio, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(P2_BTN1_GPIO, GPIO.OUT, initial=GPIO.LOW)
    for gpio in P2_LED_INPUTS.values():
        GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

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
            bg="#d0d0d0",  # Grey background
            fg="#000000",  # Black text
            activebackground="#b0b0b0",
            activeforeground="#000000",
            relief="raised",
            command=self.launch_panel1
        ).grid(row=0, column=0, padx=30)

        tk.Button(
            btn_frame, text="PANEL 2",
            font=("Arial", 18, "bold"),
            width=14, height=3,
            bg="#d0d0d0",  # Grey background
            fg="#000000",  # Black text
            activebackground="#b0b0b0",
            activeforeground="#000000",
            relief="raised",
            command=self.launch_panel2
        ).grid(row=0, column=1, padx=30)

    def launch_panel1(self):
        setup_gpio_panel1()
        self.root.destroy()
        root2 = tk.Tk()
        Panel1(root2)
        root2.mainloop()

    def launch_panel2(self):
        setup_gpio_panel2()
        self.root.destroy()
        root2 = tk.Tk()
        Panel2(root2)
        root2.mainloop()

# =============================================================
# PANEL 1
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

        self.switch_input_pins = [
            (2, 3),
            (6, 7),
            (4, 5),
            (4, 5)
        ]

        self.switch_ready_pins  = [12, 9, 8, 10]
        self.switch_ready_gpio  = [
            P1_OUTPUTS[12],
            P1_OUTPUTS[9],
            P1_OUTPUTS[8],
            P1_OUTPUTS[10]
        ]

        self.led_names       = ["AIM", "AGM GBU", "ROCK", "BOMB"]
        self.led_ground_pins = [14, 15, 16, 17]

        self.last_input_states = {}
        self.last_led_states   = [None] * 4
        self.input_active      = [False] * 4
        self.output_active     = [False] * 4

        self.btn0_last_click   = 0
        self.btn0_pending      = False

        # ── layout ──
        left  = ttk.Frame(root, padding=10)
        left.grid(row=0, column=0, sticky="nw")
        right = ttk.Frame(root, padding=10)
        right.grid(row=0, column=1, sticky="ne")

        ttk.Label(right, text="PIN ACTIVATION LOG",
                  font=("Arial", 11, "bold")).pack()
        self.log = tk.Text(right, width=34, height=18)
        self.log.pack()

        # buttons
        btn_frame = ttk.Frame(left)
        btn_frame.grid(row=0, column=0, columnspan=4, pady=10)

        self.buttons = []
        for i in range(4):
            col_frame = tk.Frame(btn_frame)
            col_frame.grid(row=0, column=i, padx=12)

            btn = tk.Button(
                col_frame, text="READY",
                width=10, height=2,
                bg="#555555", fg="white",
                font=("Arial", 10, "bold"),
                relief="raised", state="disabled",
                command=lambda i=i: self.button_pressed(i)
            )
            btn.pack()
            tk.Label(col_frame, text=self.switch_names[i],
                     font=("Arial", 9), fg="#cccccc").pack(pady=(4, 0))
            self.buttons.append(btn)

        # LEDs
        led_frame = ttk.Frame(left)
        led_frame.grid(row=2, column=0, columnspan=4, pady=15)
        self.led_widgets = []
        for i, name in enumerate(self.led_names):
            ttk.Label(led_frame, text=name).grid(row=0, column=i, padx=10)
            c   = tk.Canvas(led_frame, width=35, height=35)
            c.grid(row=1, column=i, padx=10)
            led = c.create_oval(5, 5, 30, 30, fill="gray")
            self.led_widgets.append((c, led))

        threading.Thread(target=self.gpio_monitor, daemon=True).start()

    # ── button logic ──

    def button_pressed(self, idx):
        if not self.input_active[idx]:
            self.log_event(f"[BLOCKED] No input on {self.switch_names[idx]}")
            return

        if idx == 0:
            now = time.time()
            if self.btn0_pending and (now - self.btn0_last_click) <= 2.0:
                self.btn0_pending = False
                self.toggle_output(idx)
            else:
                self.btn0_last_click = now
                self.btn0_pending    = True
                self.log_event("[M/ARM ON] Click once more within 2s to confirm")
                self.root.after(2000, self.cancel_btn0)
        else:
            self.toggle_output(idx)

    def cancel_btn0(self):
        if self.btn0_pending:
            self.btn0_pending = False
            self.log_event("[M/ARM ON] Double-click timeout — action cancelled")

    def toggle_output(self, idx):
        gpio_pin = self.switch_ready_gpio[idx]
        lp       = self.switch_ready_pins[idx]
        if not self.output_active[idx]:
            GPIO.output(gpio_pin, GPIO.HIGH)
            self.output_active[idx] = True
            self.log_event(f"Logical Pin {lp} → 3.3V (ACTIVATED)")
            self.buttons[idx].config(bg="#228822", text="ON")
        else:
            GPIO.output(gpio_pin, GPIO.LOW)
            self.output_active[idx] = False
            self.log_event(f"Logical Pin {lp} → 0V (DEACTIVATED)")
            self.buttons[idx].config(bg="#006600", text="READY")

    # ── monitor thread ──

    def gpio_monitor(self):
        while True:
            for i, pin_pair in enumerate(self.switch_input_pins):
                any_high = any(
                    GPIO.input(P1_INPUTS[lp])
                    for lp in pin_pair if lp in P1_INPUTS
                )
                if any_high != self.input_active[i]:
                    self.input_active[i] = any_high
                    for lp in pin_pair:
                        if lp in P1_INPUTS:
                            state = GPIO.input(P1_INPUTS[lp])
                            if self.last_input_states.get(lp) != bool(state):
                                self.last_input_states[lp] = bool(state)
                                self.root.after(0, self.log_event,
                                    f"Logical Pin {lp} → "
                                    f"{'3.3V (ACTIVATED)' if state else '0V (DEACTIVATED)'}")
                    self.root.after(0, self.update_button_ready, i, any_high)

            enable = GPIO.input(P1_LED_INPUTS[13])
            for i, gnd_lp in enumerate(self.led_ground_pins):
                gnd   = GPIO.input(P1_LED_INPUTS[gnd_lp])
                led_on = enable and not gnd
                if self.last_led_states[i] != led_on:
                    self.last_led_states[i] = led_on
                    self.root.after(0, self.update_led, i, led_on)
                    self.root.after(0, self.log_event,
                        f"LED {self.led_names[i]} {'ON' if led_on else 'OFF'}")
            time.sleep(0.1)

    # ── GUI updates ──

    def update_button_ready(self, idx, active):
        btn = self.buttons[idx]
        if active:
            btn.config(state="normal", bg="#00aa00", fg="white", text="READY")
            self.log_event(f"[{self.switch_names[idx]}] Input detected — button READY")
        else:
            if self.output_active[idx]:
                gpio_pin = self.switch_ready_gpio[idx]
                GPIO.output(gpio_pin, GPIO.LOW)
                self.output_active[idx] = False
                lp = self.switch_ready_pins[idx]
                self.log_event(f"Logical Pin {lp} → 0V (DEACTIVATED — input lost)")
            btn.config(state="disabled", bg="#555555", fg="white", text="READY")
            self.log_event(f"[{self.switch_names[idx]}] Input lost — button DISABLED")

    def update_led(self, idx, state):
        c, led = self.led_widgets[idx]
        c.itemconfig(led, fill="green" if state else "gray")

    def log_event(self, text):
        self.log.insert("end", text + "\n")
        self.log.see("end")

# =============================================================
# PANEL 2
# =============================================================

class Panel2(ttk.Frame):
    def toggle_btn2(self):
        if not self.grpA:
            return

        self.btn2_state = not self.btn2_state

        GPIO.output(
            self.P2_OUTPUTS["73_COOL"],
            GPIO.HIGH if self.btn2_state else GPIO.LOW
        )

        self.btn73.config(
            bg="#228822" if self.btn2_state else "#555555"
        )

    def toggle_btn3(self):
        if not self.grpA:
            return

        self.btn3_state = not self.btn3_state

        GPIO.output(
            self.P2_OUTPUTS["27T_COOL"],
            GPIO.HIGH if self.btn3_state else GPIO.LOW
        )

        self.btn27.config(
            bg="#228822" if self.btn3_state else "#555555"
        )

    def __init__(self, parent):
        super().__init__(parent)
        # self.btn2_state = True  # BTN 2 ON by default
        # self.btn3_state = False

        # ---------------- GPIO MAP (ORIGINAL PANEL 2) ----------------
        self.P2_INPUTS = {4:22, 5:23, 6:24, 7:25}

        self.P2_OUTPUTS = {
            "MODE_A":11, "MODE_C":9,
            "POWER":2, "ARM":3,
            "MAN_RANGE":12,
            "AGM_PWR":13,
            "73_COOL":4, "27T_COOL":14,
            "IND_MSL_MODE":15,
            "OUT_MODE":6,
            "EMER_UP":18, "EMER_DN":10
        }

        self.grpA = False
        self.grpB = False
        self.power_state = False
        self.arm_state = False
        self.out_mode = False
        self.unlock_time = 0
        self.emer_unlocked = False
        self.snap = False
        self.man_range_state = False
        self.agm_state = False
        self.ind_msl_state = False

        # ---------------- GPIO SETUP ----------------
        for p in self.P2_INPUTS.values():
            GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        for p in self.P2_OUTPUTS.values():
            GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

        # ---------------- BUILD UI ----------------
        self.build_ui()

        # ---------------- START MONITOR ----------------
        threading.Thread(target=self.gpio_monitor, daemon=True).start()

    # =================================================
    # GUI
    # =================================================
    def build_ui(self):

        self.pack(fill="both", expand=True, padx=8, pady=6)

        BTN_W = 12
        BTN_H = 2

        # ---------- TOP ----------
        top = ttk.Frame(self)
        top.pack(fill="x")

        # WPN REL DEALY
        wpn = ttk.Frame(top)
        wpn.pack(side="left", padx=10)

        ttk.Label(wpn, text="WPN REL DEALY",
                  font=("Arial",10,"bold")).pack()

        row = ttk.Frame(wpn)
        row.pack()

        lbls = ttk.Frame(row)
        lbls.pack(side="left")

        for t in ["5","0","3"]:
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
                                 width=BTN_W + 2, height=BTN_H,
                                 command=self.toggle_man_range)

        for b in [self.power_btn, self.arm_btn, self.man_btn]:
            b.pack(side="left", padx=6, expand=True)

        # ---------- MID ----------
        mid = ttk.Frame(self)
        mid.pack(fill="x", pady=8)



        self.agm_btn = tk.Button(mid, text="AGM PWR",
                                 width=BTN_W, height=BTN_H,
                                 command=self.toggle_agm_pwr)
        self.btn73 = tk.Button(mid, text="73 COOL",
                               width=BTN_W, height=BTN_H,
                               command=self.toggle_btn2)
        self.btn27 = tk.Button(mid, text="27T COOL",
                               width=BTN_W, height=BTN_H,
                               command=self.toggle_btn3)
        self.ind_btn = tk.Button(mid, text="IND MSL MODE",
                                 width=BTN_W + 2, height=BTN_H,
                                 command=self.toggle_ind_msl)

        for b in [self.agm_btn, self.btn73, self.btn27, self.ind_btn]:
            b.pack(side="left", padx=6, expand=True)

        # OUTPUT MODE
        self.out_mode_btn = tk.Button(self, text="SAFE",
                                      width=BTN_W, height=BTN_H,
                                      command=self.toggle_out)
        self.out_mode_btn.pack(pady=4)

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

        # group list
        self.groupA_widgets = [
            self.power_btn, self.arm_btn, self.man_btn,
            self.agm_btn, self.btn73, self.btn27,
            self.ind_btn, self.wpn_slider
        ]

    # =================================================
    # GPIO MONITOR
    # =================================================
    def gpio_monitor(self):
        while True:
            a = GPIO.input(22) or GPIO.input(23)
            b = GPIO.input(24) or GPIO.input(25)

            if a != self.grpA:
                self.grpA = a
                self.after(0, self.update_grpA)

            if b != self.grpB:
                self.grpB = b
                self.after(0, self.update_grpB)

            time.sleep(0.1)

    # =================================================
    # GROUP CONTROL
    # =================================================
    def update_grpA(self):
        state = "normal" if self.grpA else "disabled"
        color = "#228822" if self.grpA else "#555555"

        for w in self.groupA_widgets:
            w.config(state=state, bg=color)

            if not self.grpA:
                for key in ["POWER", "ARM", "MAN_RANGE",
                            "AGM_PWR", "IND_MSL_MODE"]:
                    GPIO.output(self.P2_OUTPUTS[key], GPIO.LOW)

                self.man_range_state = False
                self.agm_pwr_state = False
                self.ind_msl_state = False

                self.man_btn.config(bg="#555555")
                self.agm_btn.config(bg="#555555")
                self.ind_btn.config(bg="#555555")

    def update_grpB(self):
        state = "normal" if self.grpB else "disabled"
        color = "#228822" if self.grpB else "#555555"

        self.out_mode_btn.config(state=state, bg=color)
        self.middle_slider.config(state=state)

        if not self.grpB:
            GPIO.output(self.P2_OUTPUTS["OUT_MODE"], GPIO.LOW)
            GPIO.output(self.P2_OUTPUTS["EMER_UP"], GPIO.LOW)
            GPIO.output(self.P2_OUTPUTS["EMER_DN"], GPIO.LOW)
            self.middle_slider.set(1)

    # =================================================
    # LOGIC
    # =================================================
    def wpn_change(self, v):
        if not self.grpA:
            self.wpn_slider.set(1)
            return
        GPIO.output(self.P2_OUTPUTS["MODE_A"], GPIO.LOW)
        GPIO.output(self.P2_OUTPUTS["MODE_C"], GPIO.LOW)
        if int(v) == 2:
            GPIO.output(self.P2_OUTPUTS["MODE_A"], GPIO.HIGH)
        elif int(v) == 0:
            GPIO.output(self.P2_OUTPUTS["MODE_C"], GPIO.HIGH)

    def toggle_power(self):
        if not self.grpA: return
        self.power_state = not self.power_state
        GPIO.output(self.P2_OUTPUTS["POWER"],
                    GPIO.HIGH if self.power_state else GPIO.LOW)
        self.power_btn.config(
            text="AIR" if self.power_state else "GND"
        )

    def toggle_arm(self):
        if not self.grpA: return
        self.arm_state = not self.arm_state
        GPIO.output(self.P2_OUTPUTS["ARM"],
                    GPIO.HIGH if self.arm_state else GPIO.LOW)
        self.arm_btn.config(
            text="FWD" if self.arm_state else "TAIL"
        )

    def toggle_man_range(self):
        if not self.grpA:
            return

        self.man_range_state = not self.man_range_state
        GPIO.output(
            self.P2_OUTPUTS["MAN_RANGE"],
            GPIO.HIGH if self.man_range_state else GPIO.LOW
        )

        self.man_btn.config(
            bg="#228822" if self.man_range_state else "#555555"
        )

    def toggle_agm_pwr(self):
        if not self.grpA:
            return

        self.agm_pwr_state = not self.agm_pwr_state
        GPIO.output(
            self.P2_OUTPUTS["AGM_PWR"],
            GPIO.HIGH if self.agm_pwr_state else GPIO.LOW
        )

        self.agm_btn.config(
            bg="#228822" if self.agm_pwr_state else "#555555"
        )

    def toggle_ind_msl(self):
        if not self.grpA:
            return

        self.ind_msl_state = not self.ind_msl_state
        GPIO.output(
            self.P2_OUTPUTS["IND_MSL_MODE"],
            GPIO.HIGH if self.ind_msl_state else GPIO.LOW
        )

        self.ind_btn.config(
            bg="#228822" if self.ind_msl_state else "#555555"
        )

    def toggle_out(self):
        if not self.grpB: return
        now = time.time()
        if now - self.unlock_time <= 2:
            self.out_mode = not self.out_mode
            GPIO.output(self.P2_OUTPUTS["OUT_MODE"],
                        GPIO.HIGH if self.out_mode else GPIO.LOW)
            self.out_mode_btn.config(
                text="ARMED" if self.out_mode else "SAFE"
            )
            self.unlock_time = 0
        else:
            self.unlock_time = now

    # -------------------------------------------------
    # EMERGENCY
    # -------------------------------------------------
    def emer_unlock(self, event):
        if not self.grpB: return
        now = time.time()
        if now - self.unlock_time <= 2:
            self.emer_unlocked = True
        self.unlock_time = now

    def emer_move(self, v):
        if not self.grpB:
            self.middle_slider.set(1)
            return

        v = int(v)
        if v == 1:
            return

        if not self.emer_unlocked:
            self.middle_slider.set(1)
            return

        if v == 2:
            GPIO.output(self.P2_OUTPUTS["EMER_UP"], GPIO.HIGH)
        elif v == 0:
            GPIO.output(self.P2_OUTPUTS["EMER_DN"], GPIO.HIGH)

        self.emer_unlocked = False
        self.after(600, self.emer_reset)

    def emer_reset(self):
        GPIO.output(self.P2_OUTPUTS["EMER_UP"], GPIO.LOW)
        GPIO.output(self.P2_OUTPUTS["EMER_DN"], GPIO.LOW)
        self.middle_slider.set(1)

# =============================================================
# MAIN ENTRY POINT
# =============================================================

try:
    root = tk.Tk()
    Launcher(root)
    root.mainloop()
finally:
    GPIO.cleanup()