import tkinter as tk
from typing import Optional

from classifier import ShotClassification


class Overlay:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("cStrafe UI by CS2Kitchen")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.frame = tk.Frame(self.root, bd=2, relief="solid")
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.header_font_size = 12
        self.body_font_size = 10
        self.retro_font = "Courier"
        self.header = tk.Label(
            self.frame,
            text="cStrafe UI",
            fg="white",
            bg="#303030",
            font=(self.retro_font, self.header_font_size, "bold"),
            anchor="center",
        )
        self.header.pack(fill=tk.X)
        self.body = tk.Label(
            self.frame,
            text="Waiting for input...",
            fg="white",
            bg="#202020",
            font=(self.retro_font, self.body_font_size),
            justify=tk.CENTER,
            anchor="center",
        )
        self.body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self._offset_x: Optional[int] = None
        self._offset_y: Optional[int] = None
        self.header.bind("<ButtonPress-1>", self._on_mouse_down)
        self.header.bind("<B1-Motion>", self._on_mouse_move)
        self.is_visible = True
        self._last_text: Optional[str] = None
        self._last_bg_colour: Optional[str] = None

    def _on_mouse_down(self, event: tk.Event) -> None:
        self._offset_x = event.x
        self._offset_y = event.y

    def _on_mouse_move(self, event: tk.Event) -> None:
        if self._offset_x is not None and self._offset_y is not None:
            x = event.x_root - self._offset_x
            y = event.y_root - self._offset_y
            self.root.geometry(f"+{x}+{y}")

    def update_result(self, classification: ShotClassification) -> None:
        label = classification.label
        lines = [f"Classification: {label}"]
        if label == "Counter‑strafe" and classification.cs_time is not None and classification.shot_delay is not None:
            lines.append(f"CS time: {classification.cs_time:.0f} ms")
            lines.append(f"Shot delay: {classification.shot_delay:.0f} ms")
        elif label == "Overlap" and classification.overlap_time is not None:
            lines.append(f"Overlap: {classification.overlap_time:.0f} ms")
        elif label == "Bad" and classification.cs_time is not None and classification.shot_delay is not None:
            lines.append(f"CS time: {classification.cs_time:.0f} ms")
            lines.append(f"Shot delay: {classification.shot_delay:.0f} ms")
        colours = {
            "Counter‑strafe": "#228b22",
            "Overlap": "#ff8c00",
            "Bad": "#cc0000",
        }
        bg_colour = colours.get(label, "#202020")
        text = "\n".join(lines)
        if text == self._last_text and bg_colour == self._last_bg_colour:
            return
        self._last_text = text
        self._last_bg_colour = bg_colour
        def apply_update() -> None:
            self.frame.configure(bg=bg_colour)
            self.body.configure(text=text, bg=bg_colour)
        self.root.after(0, apply_update)

    def run(self) -> None:
        self.root.mainloop()

    def _apply_font_sizes(self) -> None:
        self.header.configure(font=(self.retro_font, self.header_font_size, "bold"))
        self.body.configure(font=(self.retro_font, self.body_font_size))

    def increase_size(self) -> None:
        if self.body_font_size < 24:
            self.body_font_size += 2
            self.header_font_size += 2
            self._apply_font_sizes()

    def decrease_size(self) -> None:
        if self.body_font_size > 8:
            self.body_font_size -= 2
            self.header_font_size = max(10, self.header_font_size - 2)
            self._apply_font_sizes()

    def toggle_visibility(self) -> None:
        def do_toggle() -> None:
            if self.is_visible:
                self.root.withdraw()
            else:
                self.root.deiconify()
            self.is_visible = not self.is_visible
        self.root.after(0, do_toggle)

    def terminate(self) -> None:
        self.root.after(0, self.root.destroy)