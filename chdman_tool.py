#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, ttk
import subprocess
import threading
import os
import sys

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

try:
    from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageDraw
    HAS_PIL = True
except Exception:
    HAS_PIL = False

VERSION = "2.2"

# ── PS1 Color Palette ─────────────────────────────────────────────────────────
BG         = "#0B0820"
BG_DEEP    = "#06041A"
PANEL_TOP  = "#1A1050"
PANEL_BOT  = "#0E0E30"
PANEL_BDR  = "#4466CC"
PANEL_BDR2 = "#2244AA"
ORANGE     = "#FF6600"
ORANGE_H   = "#FF8833"
ORANGE_D   = "#CC4400"
CYAN       = "#00CCFF"
CYAN_D     = "#0088AA"
MAGENTA    = "#FF44AA"
SUCCESS    = "#00FF66"
ERROR      = "#FF2244"
WARN       = "#FFCC00"
TEXT       = "#F0F0FF"
DIM        = "#6677BB"
DIM2       = "#334488"
GLOW       = "#3355BB"

FONT_TITLE = ("Courier New", 18, "bold")
FONT_UI    = ("Courier New", 12, "bold")
FONT_SM    = ("Courier New", 11)
FONT_XS    = ("Courier New", 10)
FONT_LOG   = ("Courier New", 11)
FONT_HUD   = ("Courier New", 10, "bold")

STATUS_META = {
    "pending":    (" ··· ", DIM),
    "converting": (" >>> ", ORANGE),
    "done":       (" [OK]", SUCCESS),
    "failed":     (" [!!]", ERROR),
}
STATUS_STRIP = {
    "pending":    DIM2,
    "converting": ORANGE,
    "done":       SUCCESS,
    "failed":     ERROR,
}

# ── Music ─────────────────────────────────────────────────────────────────────
MUSIC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "Crash Bandicoot The Wrath of Cortex Theme.mp3")
_music_on = False
_music_proc = None

def start_music():
    global _music_on
    if not os.path.exists(MUSIC_PATH) or _music_on:
        return
    _music_on = True
    def _loop():
        global _music_proc
        while _music_on:
            _music_proc = subprocess.Popen(["afplay", "--volume", "0.2", MUSIC_PATH])
            _music_proc.wait()
    threading.Thread(target=_loop, daemon=True).start()

def stop_music():
    global _music_on
    _music_on = False
    if _music_proc is not None:
        _music_proc.terminate()

def play(sound):
    path = f"/System/Library/Sounds/{sound}.aiff"
    if os.path.exists(path):
        subprocess.Popen(["afplay", path])

def find_chdman():
    for p in ["/opt/homebrew/bin/chdman", "/usr/local/bin/chdman", "/usr/bin/chdman"]:
        if os.path.isfile(p):
            return p
    return "chdman"

def find_homebrew():
    for p in ["/opt/homebrew/bin/brew", "/usr/local/bin/brew"]:
        if os.path.isfile(p):
            return p
    return None

def check_prereqs():
    """Returns list of (label, ok, detail, fix_cmd) tuples."""
    results = []

    # Homebrew
    brew = find_homebrew()
    results.append((
        "Homebrew",
        brew is not None,
        brew if brew else "Not found",
        '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    ))

    # chdman
    chdman = find_chdman()
    chdman_ok = chdman != "chdman" and os.path.isfile(chdman)
    results.append((
        "chdman  (MAME)",
        chdman_ok,
        chdman if chdman_ok else "Not found — run: brew install mame",
        "brew install mame"
    ))

    return results

def parse_drop_data(data):
    paths, data = [], data.strip()
    while data:
        if data.startswith("{"):
            end = data.index("}")
            paths.append(data[1:end])
            data = data[end + 1:].strip()
        else:
            parts = data.split(" ", 1)
            paths.append(parts[0])
            data = parts[1].strip() if len(parts) > 1 else ""
    return paths


# ═══════════════════════════════════════════════════════════════════════════════
#  PREREQ CHECK DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class PrereqDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("SYSTEM CHECK")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        results = check_prereqs()
        all_ok  = all(ok for _, ok, _, _ in results)

        # Title bar
        title_cv = tk.Canvas(self, width=420, height=54,
                             bg=BG, bd=0, highlightthickness=0)
        title_cv.pack(fill="x")
        title_cv.create_line(0, 0, 420, 0, fill=ORANGE, width=3)
        title_cv.create_text(20, 28, text="PRE-FLIGHT CHECK",
                             font=FONT_TITLE, fill=ORANGE, anchor="w")
        title_cv.create_line(0, 53, 420, 53, fill=CYAN, width=1)

        # Check rows
        for label, ok, detail, _ in results:
            row = tk.Frame(self, bg=BG, padx=20, pady=6)
            row.pack(fill="x")

            badge_color = SUCCESS if ok else ERROR
            badge_text  = "  OK  " if ok else "  !!  "
            tk.Label(row, text=badge_text, bg=badge_color, fg="#000000",
                     font=("Courier New", 10, "bold"), width=6).pack(side="left")

            tk.Label(row, text=f"  {label}", bg=BG, fg=TEXT,
                     font=FONT_UI, anchor="w", width=18).pack(side="left")

            tk.Label(row, text=detail, bg=BG, fg=DIM if ok else WARN,
                     font=FONT_XS, anchor="w").pack(side="left", padx=(4, 0))

        # Divider
        tk.Frame(self, bg=DIM2, height=1).pack(fill="x", padx=20, pady=10)

        # Bottom bar
        btn_row = tk.Frame(self, bg=BG, padx=20, pady=10)
        btn_row.pack(fill="x")

        if not all_ok:
            def _open_terminal_install():
                # Open Terminal with the first failing fix command
                for _, ok, _, fix in results:
                    if not ok and fix:
                        script = f'tell application "Terminal" to do script "{fix}"'
                        subprocess.Popen(["osascript", "-e", script])
                        break
            install_btn = tk.Label(btn_row, text=" FIX NOW → OPEN TERMINAL ",
                                   bg=ORANGE, fg="#000000",
                                   font=("Courier New", 10, "bold"),
                                   padx=8, pady=4, cursor="hand2")
            install_btn.pack(side="left")
            install_btn.bind("<Button-1>", lambda e: _open_terminal_install())

        msg = "All systems go!" if all_ok else "Some requirements are missing."
        tk.Label(btn_row, text=msg, bg=BG,
                 fg=SUCCESS if all_ok else WARN,
                 font=FONT_XS).pack(side="left", padx=12)

        close_lbl = tk.Label(btn_row, text=" CONTINUE ", bg=CYAN, fg="#000000",
                             font=("Courier New", 10, "bold"),
                             padx=8, pady=4, cursor="hand2")
        close_lbl.pack(side="right")
        close_lbl.bind("<Button-1>", lambda e: self.destroy())

        # Centre over parent
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")


# ═══════════════════════════════════════════════════════════════════════════════
#  CUSTOM WIDGET CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class GradientPanel(tk.Canvas):
    """PS1-style panel with gradient background and double border."""

    def __init__(self, parent, height=None, pad=10, **kw):
        super().__init__(parent, bd=0, highlightthickness=0, bg=BG, **kw)
        self._pad = pad
        self._fixed_h = height
        self._content = tk.Frame(self, bg=PANEL_BOT)
        # inner content sits on top of the canvas
        self._content_win = self.create_window(pad + 4, pad + 4, anchor="nw",
                                                window=self._content)
        self.bind("<Configure>", self._redraw)
        self._content.bind("<Configure>", self._on_content_resize)

    @property
    def content(self):
        return self._content

    def _on_content_resize(self, e):
        # resize canvas to fit content + padding + border
        w = e.width + (self._pad + 4) * 2
        h = e.height + (self._pad + 4) * 2
        if self._fixed_h:
            h = max(h, self._fixed_h)
        self.config(width=w, height=h)
        self._redraw(None)

    def _redraw(self, e):
        self.delete("bg")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            return

        p = self._pad

        # Outer glow border
        self.create_rectangle(p-2, p-2, w-p+2, h-p+2,
                              outline=PANEL_BDR2, width=1, tags="bg")
        # Main bright border
        self.create_rectangle(p, p, w-p, h-p,
                              outline=PANEL_BDR, width=2, tags="bg")

        # Gradient fill
        x1, y1 = p + 2, p + 2
        x2, y2 = w - p - 2, h - p - 2
        steps = 30
        dy = max(1, (y2 - y1) / steps)
        for i in range(steps):
            t = i / steps
            r = int(0x1A + (0x0E - 0x1A) * t)
            g = int(0x10 + (0x0E - 0x10) * t)
            b = int(0x50 + (0x30 - 0x50) * t)
            color = f"#{max(0,r):02x}{max(0,g):02x}{max(0,b):02x}"
            cy = y1 + i * dy
            self.create_rectangle(x1, cy, x2, min(cy + dy + 1, y2),
                                  fill=color, outline=color, tags="bg")

        # Corner accents (small L-shaped brackets)
        sz = 8
        for cx, cy, dx, dy_c in [(x1, y1, 1, 1), (x2, y1, -1, 1),
                                   (x1, y2, 1, -1), (x2, y2, -1, -1)]:
            self.create_line(cx, cy, cx + sz*dx, cy, fill=CYAN, width=1, tags="bg")
            self.create_line(cx, cy, cx, cy + sz*dy_c, fill=CYAN, width=1, tags="bg")

        # Reposition content on top of gradient
        self.itemconfig(self._content_win, width=max(1, w - (p+4)*2))
        self.tag_lower("bg")


class GlowLabel(tk.Canvas):
    """Text label with a soft glow effect behind it."""

    def __init__(self, parent, text, font=FONT_UI, fg=CYAN, glow_color=None,
                 bg_color=BG, **kw):
        self._text = text
        self._font = font
        self._fg = fg
        self._glow = glow_color or GLOW
        super().__init__(parent, bg=bg_color, bd=0, highlightthickness=0,
                         height=28, **kw)
        self.bind("<Configure>", self._draw)

    def _draw(self, e=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        y = h // 2

        # Decorative line across full width
        self.create_line(0, y, w, y, fill=DIM2, width=1)

        # Measure text to draw background patch behind it
        tid = self.create_text(0, 0, text=self._text, font=self._font, anchor="nw")
        bbox = self.bbox(tid)
        self.delete(tid)
        tw = bbox[2] - bbox[0] + 16 if bbox else 100

        # Background patch to cover the line
        self.create_rectangle(0, 0, tw, h, fill=self.cget("bg"), outline="", tags="patch")

        # Glow layers
        for offset, alpha_hex in [(2, "44"), (1, "77")]:
            gc = self._glow
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                self.create_text(8 + dx, y + dy, text=self._text,
                                 font=self._font, fill=gc, anchor="w")

        # Main text
        self.create_text(8, y, text=self._text, font=self._font,
                         fill=self._fg, anchor="w")


class HealthBar(tk.Canvas):
    """Game-style segmented progress bar."""

    SEGMENTS = 20
    SEG_GAP = 2

    def __init__(self, parent, width=200, height=18, **kw):
        super().__init__(parent, width=width, height=height, bg=BG,
                         bd=0, highlightthickness=0, **kw)
        self._fill = 0.0  # 0.0 to 1.0
        self._animating = False
        self._anim_id = None
        self.bind("<Configure>", lambda e: self._draw())

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()

        # Trough border
        self.create_rectangle(0, 0, w-1, h-1, outline=DIM2, width=1)

        seg_w = (w - 4 - (self.SEGMENTS - 1) * self.SEG_GAP) / self.SEGMENTS
        filled = int(self._fill * self.SEGMENTS)

        for i in range(self.SEGMENTS):
            x1 = 2 + i * (seg_w + self.SEG_GAP)
            x2 = x1 + seg_w
            if i < filled:
                # Gradient within each segment
                color = ORANGE if i < self.SEGMENTS * 0.7 else WARN
                self.create_rectangle(x1, 3, x2, h-3, fill=color, outline="")
                # Highlight on top half
                self.create_rectangle(x1, 3, x2, h//2, fill=ORANGE_H, outline="")
            else:
                self.create_rectangle(x1, 3, x2, h-3, fill="#0A0A20", outline="")

    def start_indeterminate(self):
        self._animating = True
        self._bounce_pos = 0
        self._bounce_dir = 1
        self._animate()

    def _animate(self):
        if not self._animating:
            return
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        self.create_rectangle(0, 0, w-1, h-1, outline=DIM2, width=1)

        seg_w = (w - 4 - (self.SEGMENTS - 1) * self.SEG_GAP) / self.SEGMENTS

        # Moving highlight of 5 segments
        highlight_width = 5
        for i in range(self.SEGMENTS):
            x1 = 2 + i * (seg_w + self.SEG_GAP)
            x2 = x1 + seg_w
            dist = abs(i - self._bounce_pos)
            if dist < highlight_width:
                intensity = 1.0 - (dist / highlight_width)
                r = int(0x0A + (0xFF - 0x0A) * intensity)
                g = int(0x0A + (0x66 - 0x0A) * intensity)
                b = 0x20
                color = f"#{r:02x}{g:02x}{b:02x}"
                self.create_rectangle(x1, 3, x2, h-3, fill=color, outline="")
                # Top highlight
                rh = min(255, int(r * 1.2))
                gh = min(255, int(g * 1.2))
                self.create_rectangle(x1, 3, x2, h//2,
                                      fill=f"#{rh:02x}{gh:02x}{b:02x}", outline="")
            else:
                self.create_rectangle(x1, 3, x2, h-3, fill="#0A0A20", outline="")

        self._bounce_pos += self._bounce_dir * 0.6
        if self._bounce_pos >= self.SEGMENTS - 1:
            self._bounce_dir = -1
        elif self._bounce_pos <= 0:
            self._bounce_dir = 1

        self._anim_id = self.after(40, self._animate)

    def stop(self):
        self._animating = False
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None
        self._fill = 0.0
        self._draw()


class RetroBtn(tk.Frame):
    """PS1-style button with gradient fill and glow hover."""

    def __init__(self, parent, text, command, style="primary", width=None, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._text = text
        self._command = command
        self._style = style
        self._enabled = True

        cfg = {
            "primary": (ORANGE, "#000000", ORANGE_H, ORANGE_D),
            "ghost":   (PANEL_TOP, DIM, "#1E1660", "#0C0C25"),
            "danger":  (ERROR, "#000000", "#FF5566", "#CC1133"),
        }
        self._bg_c, self._fg, self._hover, self._press_c = cfg[style]

        tw = len(text) * 8 + 28
        th = 32
        if width:
            tw = width

        self._cv = tk.Canvas(self, width=tw, height=th, bg=BG,
                             bd=0, highlightthickness=0, cursor="hand2")
        self._cv.pack()
        self._tw = tw
        self._th = th

        self._cv.bind("<Enter>",          self._on_enter)
        self._cv.bind("<Leave>",          self._on_leave)
        self._cv.bind("<Button-1>",       self._on_press)
        self._cv.bind("<ButtonRelease-1>", self._on_release)
        self._cv.bind("<Map>",            lambda e: self._draw(self._bg_c))

    def _draw(self, base_color, pressed=False):
        cv = self._cv
        cv.delete("all")
        w, h = self._tw, self._th

        if pressed:
            cv.create_rectangle(1, 1, w-1, h-1, outline=DIM2, width=1)
            cv.create_rectangle(2, 2, w-2, h-2, fill=self._press_c, outline="")
            cv.create_text(w//2 + 1, h//2 + 1, text=self._text,
                           font=FONT_UI, fill=self._fg)
        else:
            if self._style == "primary" and self._enabled:
                cv.create_rectangle(0, 0, w, h, outline=ORANGE_D, width=1)
            bdr = PANEL_BDR if self._style == "ghost" else (
                "#FFFFFF" if base_color == self._hover else "#DDAA44")
            cv.create_rectangle(1, 1, w-2, h-2, outline=bdr, width=1)

            for i in range(h - 4):
                t = i / max(1, h - 4)
                r0 = int(base_color[1:3], 16)
                g0 = int(base_color[3:5], 16)
                b0 = int(base_color[5:7], 16)
                factor = (1.2 - t * 0.4) if t < 0.5 else (1.0 - (t - 0.5) * 0.6)
                r = min(255, int(r0 * factor))
                g = min(255, int(g0 * factor))
                b = min(255, int(b0 * factor))
                cv.create_line(2, 2 + i, w - 2, 2 + i,
                               fill=f"#{r:02x}{g:02x}{b:02x}")
            cv.create_text(w//2, h//2, text=self._text,
                           font=FONT_UI, fill=self._fg)

    def _on_enter(self, e):
        if self._enabled:
            self._draw(self._hover)

    def _on_leave(self, e):
        if self._enabled:
            self._draw(self._bg_c)

    def _on_press(self, e):
        if not self._enabled:
            return
        self._draw(self._press_c, pressed=True)
        play("Tink")
        self.after(80, self._command)

    def _on_release(self, e):
        if self._enabled:
            self._draw(self._bg_c)

    def disable(self, label=None):
        self._enabled = False
        if label:
            self._text = label
        self._cv.config(cursor="arrow")
        cv = self._cv
        cv.delete("all")
        w, h = self._tw, self._th
        cv.create_rectangle(1, 1, w-2, h-2, outline=DIM2, width=1)
        cv.create_rectangle(2, 2, w-2, h-2, fill="#111130", outline="")
        cv.create_text(w//2, h//2, text=self._text, font=FONT_UI, fill=DIM2)

    def enable(self, label=None):
        self._enabled = True
        if label:
            self._text = label
        self._cv.config(cursor="hand2")
        self._draw(self._bg_c)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

BaseClass = TkinterDnD.Tk if HAS_DND else tk.Tk

class App(BaseClass):
    def __init__(self):
        super().__init__()
        self.title("CHDMAN")
        self.configure(bg=BG)
        self.resizable(True, False)

        self.jobs       = []
        self.out_folder = tk.StringVar()
        self._running   = False
        self._row_index = 0
        self._muted     = False
        self._pulse_id  = None
        self._current_proc = None

        self._build_header()
        self._build_queue()
        self._build_output_folder()
        self._build_run()
        self._build_log()
        self._build_hud()

        if HAS_DND:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)

        start_music()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(300, self._run_prereq_check)
        self.update_idletasks()
        self.minsize(720, self.winfo_reqheight())

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        BANNER_H = 140
        self._banner_pil = None

        if HAS_PIL:
            try:
                img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "Picture.jpg")
                self._banner_pil = Image.open(img_path)
            except Exception:
                pass

        canvas = tk.Canvas(self, height=BANNER_H, bd=0, highlightthickness=0, bg=BG)
        canvas.pack(fill="x")
        self._banner_canvas = canvas
        self._banner_h = BANNER_H
        self._banner_photo = None
        canvas.bind("<Configure>", self._redraw_banner)

    def _redraw_banner(self, e=None):
        canvas = self._banner_canvas
        w = canvas.winfo_width()
        h = self._banner_h
        if w < 2:
            return
        canvas.delete("all")

        if self._banner_pil and HAS_PIL:
            try:
                resample = getattr(Image, "Resampling", Image).LANCZOS
                img = self._banner_pil.resize((w, h), resample)
                img = ImageEnhance.Brightness(img).enhance(0.35)
                img = img.filter(ImageFilter.GaussianBlur(radius=2))

                vignette = Image.new("L", (w, h), 0)
                draw = ImageDraw.Draw(vignette)
                max_i = min(w // 2, h // 2)
                for i in range(max_i):
                    alpha = int(255 * (i / max_i))
                    draw.rectangle([i, i, w - i - 1, h - i - 1], outline=alpha)
                img = Image.composite(img, Image.new("RGB", img.size, "#050318"), vignette)

                self._banner_photo = ImageTk.PhotoImage(img)
                canvas.create_image(0, 0, anchor="nw", image=self._banner_photo)
            except Exception:
                pass

        # Bottom gradient fade
        for i in range(30):
            r = int(0x0B * (1 - i/30))
            g = int(0x08 * (1 - i/30))
            b = int(0x20 * (1 - i/30))
            y = h - 30 + i
            canvas.create_line(0, y, w, y, fill=f"#{r:02x}{g:02x}{max(1,b):02x}")

        # Glow title
        tx, ty = 24, h // 2 - 16
        for dx, dy, c in [(-2,0,GLOW),(2,0,GLOW),(0,-2,GLOW),(0,2,GLOW),
                           (-1,-1,GLOW),(1,1,GLOW)]:
            canvas.create_text(tx+dx, ty+dy, text="CHDMAN  CREATECD",
                               font=FONT_TITLE, fill=c, anchor="w")
        canvas.create_text(tx, ty, text="CHDMAN  CREATECD",
                           font=FONT_TITLE, fill=ORANGE, anchor="w")
        canvas.create_text(tx + 2, ty + 30, text="BATCH DISC IMAGE CONVERTER",
                           font=FONT_XS, fill=TEXT, anchor="w")

        # Lines
        canvas.create_line(0, 0, w, 0, fill=ORANGE, width=4)
        canvas.create_line(0, h-1, w, h-1, fill=CYAN, width=2)

    # ── Queue ─────────────────────────────────────────────────────────────────
    def _build_queue(self):
        wrap = tk.Frame(self, bg=BG, padx=20, pady=16)
        wrap.pack(fill="x")

        # Section header with glow
        hdr = tk.Frame(wrap, bg=BG)
        hdr.pack(fill="x", pady=(0, 10))
        GlowLabel(hdr, "[ QUEUE ]", font=FONT_UI, fg=CYAN).pack(
            side="left", fill="x", expand=True)
        RetroBtn(hdr, "  + ADD FILES  ", self._add_files,
                 style="ghost").pack(side="right")

        # Panel
        self._queue_panel = GradientPanel(wrap, height=210)
        self._queue_panel.pack(fill="x")

        inner = self._queue_panel.content

        self._queue_canvas = tk.Canvas(inner, bg=PANEL_BOT, bd=0,
                                       highlightthickness=0, height=180)
        sb = ttk.Scrollbar(inner, orient="vertical",
                           command=self._queue_canvas.yview)
        self._queue_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._queue_canvas.pack(side="left", fill="both", expand=True)

        self._queue_frame = tk.Frame(self._queue_canvas, bg=PANEL_BOT)
        self._queue_win = self._queue_canvas.create_window(
            (0, 0), window=self._queue_frame, anchor="nw")
        self._queue_frame.bind("<Configure>", lambda e:
            self._queue_canvas.configure(
                scrollregion=self._queue_canvas.bbox("all")))
        self._queue_canvas.bind("<Configure>", lambda e:
            self._queue_canvas.itemconfig(self._queue_win, width=e.width))

        self._empty_lbl = tk.Label(
            self._queue_frame,
            text="\n  //  DROP .CUE / .ISO FILES HERE  //\n\n  or click  [ + ADD FILES ]\n",
            bg=PANEL_BOT, fg=DIM, font=FONT_SM)
        self._empty_lbl.pack(expand=True, pady=20)

    # ── Output folder ─────────────────────────────────────────────────────────
    def _build_output_folder(self):
        wrap = tk.Frame(self, bg=BG, padx=20, pady=16)
        wrap.pack(fill="x")

        GlowLabel(wrap, "[ OUTPUT FOLDER ]", font=FONT_UI, fg=CYAN).pack(
            fill="x", pady=(0, 4))
        tk.Label(wrap, text="  leave empty to save .chd next to each input file",
                 bg=BG, fg=DIM2, font=FONT_XS).pack(anchor="w", pady=(0, 8))

        panel = GradientPanel(wrap, height=50)
        panel.pack(fill="x")
        inner = panel.content

        entry = tk.Entry(inner, textvariable=self.out_folder,
                         bg=PANEL_BOT, fg=TEXT, font=FONT_SM,
                         insertbackground=ORANGE, bd=0, highlightthickness=0)
        entry.pack(side="left", fill="x", expand=True, padx=(6, 0), pady=4)

        for label, cmd in [("BROWSE", self._pick_folder),
                           ("CLEAR",  lambda: self.out_folder.set(""))]:
            b = tk.Label(inner, text=label, bg=PANEL_BOT, fg=CYAN,
                         font=FONT_XS, padx=10, cursor="hand2")
            b.pack(side="right")
            b.bind("<Button-1>", lambda e, c=cmd: c())
            b.bind("<Enter>",    lambda e, w=b: w.config(fg=MAGENTA))
            b.bind("<Leave>",    lambda e, w=b: w.config(fg=CYAN))

    # ── Run bar ───────────────────────────────────────────────────────────────
    def _build_run(self):
        # Decorative divider
        div = tk.Canvas(self, height=6, bg=BG, bd=0, highlightthickness=0)
        div.pack(fill="x", padx=20)
        div.bind("<Configure>", lambda e: (
            div.delete("all"),
            div.create_line(0, 3, e.width, 3, fill=DIM2, width=1),
            div.create_line(0, 4, e.width, 4, fill=PANEL_BDR2, width=1)
        ))

        row = tk.Frame(self, bg=BG, padx=20, pady=12)
        row.pack(fill="x")

        self.run_btn = RetroBtn(row, "  CONVERT ALL  ", self._run_all, width=180)
        self.run_btn.pack(side="left")

        clr = RetroBtn(row, " CLEAR DONE ", self._clear_done, style="ghost")
        clr.pack(side="left", padx=(10, 0))

        self._mute_btn = RetroBtn(row, " MUSIC ON ", self._toggle_mute,
                                  style="ghost")
        self._mute_btn.pack(side="right")

        RetroBtn(row, " INSTALL CHDMAN ", self._install_chdman,
                 style="ghost").pack(side="right", padx=(0, 8))

        self.status_lbl = tk.Label(row, text="", bg=BG, fg=DIM, font=FONT_SM)
        self.status_lbl.pack(side="left", padx=14)

        # Health bar — full width row below buttons
        self.progress = HealthBar(self, height=10)
        self.progress.pack(fill="x", padx=20, pady=(0, 6))

    # ── Log ───────────────────────────────────────────────────────────────────
    def _build_log(self):
        wrap = tk.Frame(self, bg=BG, padx=20, pady=8)
        wrap.pack(fill="both", expand=True)

        GlowLabel(wrap, "[ CONSOLE OUTPUT ]", font=FONT_UI, fg=CYAN).pack(
            fill="x", pady=(0, 8))

        log_panel = GradientPanel(wrap, height=200)
        log_panel.pack(fill="x")

        self.log = tk.Text(log_panel.content, height=10, width=72,
                           bg="#050318", fg="#9999DD",
                           font=FONT_LOG, bd=0,
                           highlightthickness=0,
                           selectbackground=ORANGE,
                           insertbackground=ORANGE,
                           state="disabled", padx=8, pady=6)
        self.log.pack(fill="both", expand=True)
        self.log.tag_config("ok",  foreground=SUCCESS)
        self.log.tag_config("err", foreground=ERROR)
        self.log.tag_config("dim", foreground=DIM)
        self.log.tag_config("hdr", foreground=ORANGE, font=("Courier New", 11, "bold"))

    # ── HUD bar ───────────────────────────────────────────────────────────────
    def _build_hud(self):
        hud = tk.Canvas(self, height=28, bg=BG_DEEP, bd=0, highlightthickness=0)
        hud.pack(fill="x", side="bottom")
        self._hud = hud

        # Top line
        hud.create_line(0, 0, 4000, 0, fill=ORANGE, width=3)

        self._hud_items = {}
        hud.bind("<Configure>", lambda e: self._update_hud())
        self._update_hud()

    def _update_hud(self):
        hud = self._hud
        hud.delete("stats")
        total  = len(self.jobs)
        done   = sum(1 for j in self.jobs if j["status"] == "done")
        failed = sum(1 for j in self.jobs if j["status"] == "failed")
        conv   = sum(1 for j in self.jobs if j["status"] == "converting")
        pend   = sum(1 for j in self.jobs if j["status"] == "pending")

        x = 16
        for label, val, color in [
            ("FILES", total, TEXT),
            ("PENDING", pend, DIM),
            ("ACTIVE", conv, ORANGE),
            ("DONE", done, SUCCESS),
            ("FAILED", failed, ERROR),
        ]:
            hud.create_text(x, 15, text=f"{label}:", font=FONT_HUD,
                            fill=DIM2, anchor="w", tags="stats")
            x += len(label) * 7 + 8
            hud.create_text(x, 15, text=str(val), font=FONT_HUD,
                            fill=color, anchor="w", tags="stats")
            x += 30

        # Version on right edge
        right = max(hud.winfo_width() - 16, 700)
        hud.create_text(right, 15, text=f"v{VERSION}", font=FONT_HUD,
                        fill=DIM2, anchor="e", tags="stats")

    # ── File adding ───────────────────────────────────────────────────────────
    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select CUE / ISO files",
            filetypes=[("Disc images", "*.cue *.iso"), ("CUE files", "*.cue"),
                       ("ISO files", "*.iso"), ("All files", "*.*")])
        for p in paths:
            self._enqueue(p)

    def _pick_folder(self):
        d = filedialog.askdirectory(title="Select output folder")
        if d:
            self.out_folder.set(d)

    def _on_drop(self, event):
        for path in parse_drop_data(event.data):
            if os.path.isdir(path):
                # Scan dropped folder for disc images
                for root, _, files in os.walk(path):
                    for f in sorted(files):
                        if f.lower().endswith((".cue", ".iso")):
                            self._enqueue(os.path.join(root, f))
            elif path.lower().endswith((".cue", ".iso")):
                self._enqueue(path)

    def _enqueue(self, cue_path):
        if any(j["cue"] == cue_path for j in self.jobs):
            return

        job = {"cue": cue_path, "status": "pending"}
        self.jobs.append(job)
        self._empty_lbl.pack_forget()

        row_bg = "#111140" if self._row_index % 2 else PANEL_BOT
        self._row_index += 1

        row = tk.Frame(self._queue_frame, bg=row_bg)
        row.pack(fill="x")
        job["row"] = row

        # Colored left status strip
        strip = tk.Frame(row, bg=STATUS_STRIP["pending"], width=4)
        strip.pack(side="left", fill="y")
        strip.pack_propagate(False)
        job["strip"] = strip

        # Status badge
        icon, color = STATUS_META["pending"]
        job["icon_lbl"] = tk.Label(row, text=icon, bg=row_bg, fg=color,
                                   font=("Courier New", 10, "bold"), width=6)
        job["icon_lbl"].pack(side="left", padx=(4, 0))

        # Filename
        name = os.path.basename(cue_path)
        job["name_lbl"] = tk.Label(row, text=name, bg=row_bg, fg=TEXT,
                                   font=FONT_SM, anchor="w")
        job["name_lbl"].pack(side="left", fill="x", expand=True, padx=6, pady=6)

        # Directory
        d = os.path.dirname(cue_path)
        if len(d) > 35:
            d = "..." + d[-34:]
        tk.Label(row, text=d, bg=row_bg, fg=DIM2,
                 font=FONT_XS, anchor="e").pack(side="left", padx=(0, 6))

        # Remove button
        rm = tk.Label(row, text=" X ", bg=row_bg, fg=DIM,
                      font=FONT_XS, cursor="hand2")
        rm.pack(side="right", padx=4)
        rm.bind("<Button-1>", lambda e, j=job: self._remove_job(j))
        rm.bind("<Enter>",    lambda e: rm.config(fg=ERROR))
        rm.bind("<Leave>",    lambda e: rm.config(fg=DIM))

        sep = tk.Frame(self._queue_frame, bg=DIM2, height=1)
        sep.pack(fill="x")
        job["sep"] = sep
        self._update_hud()

    def _remove_job(self, job):
        if job["status"] == "converting":
            return
        job["row"].destroy()
        job["sep"].destroy()
        self.jobs.remove(job)
        if not self.jobs:
            self._empty_lbl.pack(expand=True, pady=20)
        self._update_hud()

    def _clear_done(self):
        for job in [j for j in self.jobs if j["status"] in ("done", "failed")]:
            self._remove_job(job)

    # ── Status helpers ────────────────────────────────────────────────────────
    def _set_job_status(self, job, status):
        job["status"] = status
        icon, color = STATUS_META[status]
        job["icon_lbl"].config(text=icon, fg=color)
        job["strip"].config(bg=STATUS_STRIP[status])
        self._update_hud()

    def _set_status(self, text, color=DIM):
        self.status_lbl.config(text=text, fg=color)

    def _log(self, text, tag=None):
        self.log.configure(state="normal")
        self.log.insert("end", text, tag or "")
        self.log.see("end")
        self.log.configure(state="disabled")

    # ── Pulse animation for converting jobs ───────────────────────────────────
    def _start_pulse(self):
        self._pulse_state = True
        self._pulse()

    def _pulse(self):
        if not self._running:
            return
        self._pulse_state = not self._pulse_state
        for job in self.jobs:
            if job["status"] == "converting":
                txt = " >>> " if self._pulse_state else " >>  "
                job["icon_lbl"].config(text=txt)
        self._pulse_id = self.after(500, self._pulse)

    def _stop_pulse(self):
        if self._pulse_id:
            self.after_cancel(self._pulse_id)
            self._pulse_id = None

    # ── Conversion ────────────────────────────────────────────────────────────
    def _derive_out(self, cue):
        folder = self.out_folder.get().strip()
        base   = os.path.splitext(os.path.basename(cue))[0]
        return os.path.join(folder if folder else os.path.dirname(cue),
                            base + ".chd")

    def _run_all(self):
        pending = [j for j in self.jobs if j["status"] == "pending"]
        if not pending:
            return
        self._running = True
        self.run_btn.disable("  RUNNING...  ")
        self.progress.start_indeterminate()
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self._start_pulse()
        self._convert_next(pending)

    def _convert_next(self, queue):
        if not queue:
            self._finish_all()
            return
        job, rest = queue[0], queue[1:]
        self._set_job_status(job, "converting")
        self._set_status(f">> {os.path.basename(job['cue'])}", ORANGE)
        out = self._derive_out(job["cue"])
        self._log(f"\n{'='*60}\n", "dim")
        self._log(f"  FILE : {os.path.basename(job['cue'])}\n", "hdr")
        self._log(f"  IN   : {job['cue']}\n", "dim")
        self._log(f"  OUT  : {out}\n", "dim")
        self._log(f"{'='*60}\n\n", "dim")
        threading.Thread(target=self._worker, args=(job, out, rest), daemon=True).start()

    def _worker(self, job, out, rest):
        # Skip if the output file is already there
        if os.path.exists(out):
            self.after(0, self._set_job_status, job, "done")
            self.after(0, self._log,
                       "  >> SKIPPED — output file already exists\n", "ok")
            self.after(0, self._convert_next, rest)
            return

        # Re-resolve chdman each run, in case it was just installed
        cmd = [find_chdman(), "createcd", "-i", job["cue"], "-o", out]
        try:
            out_dir = os.path.dirname(out)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            self._current_proc = proc
            for line in proc.stdout:
                self.after(0, self._log, "  " + line)
            proc.wait()
            if proc.returncode == 0:
                self.after(0, self._set_job_status, job, "done")
                self.after(0, self._log, "\n  >> DONE\n", "ok")
                self.after(0, play, "Ping")
            else:
                self.after(0, self._set_job_status, job, "failed")
                self.after(0, self._log,
                           f"\n  !! FAILED (exit {proc.returncode})\n", "err")
                self.after(0, play, "Basso")
        except FileNotFoundError:
            self.after(0, self._set_job_status, job, "failed")
            self.after(0, self._log,
                       "  !! ERROR: 'chdman' not found — click INSTALL CHDMAN\n", "err")
            self.after(0, play, "Basso")
        finally:
            self._current_proc = None
            self.after(0, self._convert_next, rest)

    def _finish_all(self):
        self._running = False
        self._stop_pulse()
        self.progress.stop()
        self.run_btn.enable("  CONVERT ALL  ")
        done   = sum(1 for j in self.jobs if j["status"] == "done")
        failed = sum(1 for j in self.jobs if j["status"] == "failed")
        if failed == 0:
            self._set_status(f">> ALL {done} DONE!", SUCCESS)
            play("Hero")
        else:
            self._set_status(f">> {done} OK  //  {failed} FAILED", ERROR)
            play("Basso")
        self._update_hud()

    def _run_prereq_check(self):
        PrereqDialog(self)

    def _install_chdman(self):
        # Check if chdman is already available
        found = find_chdman()
        if found != "chdman" and os.path.isfile(found):
            self._log(f"\n  ✅ chdman is already installed at: {found}\n", "ok")
            play("Ping")
            return
        # Not found — open Terminal and install via Homebrew
        script = 'tell application "Terminal" to do script "brew install mame && echo \\"\\n✅ chdman installed! You can close this window.\\""'
        subprocess.Popen(["osascript", "-e", script])

    def _toggle_mute(self):
        self._muted = not self._muted
        if self._muted:
            stop_music()
            self._mute_btn._text = " MUSIC OFF "
            self._mute_btn._draw(self._mute_btn._bg_c)
        else:
            start_music()
            self._mute_btn._text = " MUSIC ON "
            self._mute_btn._draw(self._mute_btn._bg_c)

    def _on_close(self):
        stop_music()
        # Kill any running conversion so it doesn't linger in the background
        proc = self._current_proc
        if proc is not None:
            try:
                proc.terminate()
            except OSError:
                pass
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
