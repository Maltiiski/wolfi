import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_DIR / "assets"

DOG_SIZE = 160
FRAME_INTERVAL_MS = 5000
RAM_CHECK_INTERVAL_MS = 1000

CONDITIONS = {
    "relaxed": [
        "wolf_relaxed1.png",
        "wolf_relaxed2.png",
        "wolf_relaxed3.png",
        "wolf_relaxed2.png",
    ],
    "worried": [
        "wolf_active1.png",
        "wolf_active2.png",
        "wolf_active3.png",
        "wolf_active2.png",
    ],
    "panic": [
        "wolf_panic1.png",
        "wolf_panic2.png",
        "wolf_panic3.png",
        "wolf_panic2.png",
    ],
}


def get_ram_usage():
    """Return system RAM usage as a percentage."""

    values = {}

    with open("/proc/meminfo", "r", encoding="utf-8") as file:
        for line in file:
            key, value = line.split(":", 1)
            values[key] = int(value.strip().split()[0])

    total = values["MemTotal"]
    available = values["MemAvailable"]
    used = total - available

    return used / total * 100


def get_condition(ram_percent):
    """Choose a condition based on RAM usage."""

    if ram_percent >= 80:
        return "panic"
    elif ram_percent >= 60:
        return "worried"
    else:
        return "relaxed"


class Wolfi(Gtk.Application):

    def __init__(self):
        super().__init__(application_id="com.wolfi.RAMMonitor")

        self.window = None
        self.image = None
        self.ram_label = None

        self.textures = {}
        self.current_condition = None
        self.frame_index = 0

    def do_activate(self):

        for condition, filenames in CONDITIONS.items():
            self.textures[condition] = []

            for filename in filenames:
                path = ASSETS_DIR / filename

                if not path.is_file():
                    print(f"Missing image: {path}")
                    return

                texture = Gdk.Texture.new_from_filename(str(path))
                self.textures[condition].append(texture)

        css = Gtk.CssProvider()
        css.load_from_data(b"""
            window {
                background-color: transparent;
            }

            picture {
                background-color: transparent;
            }
        """)

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.image = Gtk.Picture()
        self.image.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.image.set_can_shrink(True)
        self.image.set_size_request(DOG_SIZE, DOG_SIZE)

        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("Wolfi")
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.ram_label = Gtk.Label(label="RAM: --%")
        self.ram_label.set_halign(Gtk.Align.CENTER)
        self.ram_label.set_visible(False)

        container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=4,
        )
        container.set_halign(Gtk.Align.CENTER)

        container.append(self.ram_label)
        container.append(self.image)

        self.window.set_child(container)

        hover = Gtk.EventControllerMotion()

        def on_mouse_enter(controller, x, y):
            self.ram_label.set_visible(True)
            self.update_ram_label()

        def on_mouse_leave(controller):
            self.ram_label.set_visible(False)

        hover.connect("enter", on_mouse_enter)
        hover.connect("leave", on_mouse_leave)

        container.add_controller(hover)

        drag = Gtk.GestureClick()
        drag.set_button(1)

        def on_drag_begin(gesture, n_press, x, y):
            event = gesture.get_current_event()
            if event is None:
                return

            device = gesture.get_current_event_device()
            surface = self.window.get_surface()

            if surface is None:
                return

            toplevel = surface
            if isinstance(toplevel, Gdk.Toplevel):
                toplevel.begin_move(
                    device,
                    1,
                    x,
                    y,
                    event.get_time(),
                )

        drag.connect("pressed", on_drag_begin)
        self.image.add_controller(drag)

        self.window.present()

        self.update_condition()

        GLib.timeout_add(
            FRAME_INTERVAL_MS,
            self.advance_frame,
        )

        GLib.timeout_add(
            RAM_CHECK_INTERVAL_MS,
            self.update_condition,
        )

        print("Wolfi is running!")

    def update_ram_label(self):
        ram_percent = get_ram_usage()
        self.ram_label.set_text(f"RAM: {ram_percent:.1f}%")

    def update_condition(self):

        ram_percent = get_ram_usage()
        condition = get_condition(ram_percent)

        if condition != self.current_condition:
            self.current_condition = condition
            self.frame_index = 0

            self.image.set_paintable(
                self.textures[condition][self.frame_index]
            )

            print(
                f"RAM: {ram_percent:.1f}% | "
                f"Condition: {condition}"
            )

        return GLib.SOURCE_CONTINUE

    def advance_frame(self):

        if self.current_condition is None:
            return GLib.SOURCE_CONTINUE

        frames = self.textures[self.current_condition]

        self.frame_index = (
            self.frame_index + 1
        ) % len(frames)

        self.image.set_paintable(frames[self.frame_index])

        return GLib.SOURCE_CONTINUE


app = Wolfi()
app.run()