import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk

from pathlib import Path

# -------------------------
# Configuration
# -------------------------

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


# -------------------------
# RAM monitoring
# -------------------------

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


# -------------------------
# Wolfi application
# -------------------------

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

        # Load all animation images once
        for condition, filenames in CONDITIONS.items():
            self.textures[condition] = []

            for filename in filenames:
                path = ASSETS_DIR / filename

                if not path.is_file():
                    print(f"Missing image: {path}")
                    return

                texture = Gdk.Texture.new_from_filename(str(path))
                self.textures[condition].append(texture)

        # Transparent widget styling
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

        # Create dog image
        self.image = Gtk.Picture()
        self.image.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.image.set_can_shrink(True)
        self.image.set_size_request(DOG_SIZE, DOG_SIZE)

        # Create window
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("Wolfi")
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.set_child(self.image)

        # Allow dragging Wolfi with the mouse
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

        # Initialize the correct condition
        self.update_condition()

        # Start timers
        GLib.timeout_add(
            FRAME_INTERVAL_MS,
            self.advance_frame,
        )

        GLib.timeout_add(
            RAM_CHECK_INTERVAL_MS,
            self.update_condition,
        )

        print("Wolfi is running!")

    def update_condition(self):

        ram_percent = get_ram_usage()
        condition = get_condition(ram_percent)

        # Switch animation only if the condition changes
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