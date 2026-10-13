import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_DIR / "assets"

DOG_SIZE = 160
FRAME_INTERVAL_MS = 5000

# gambar2 keren
FRAMES = [
    "wolf_relaxed1.png",
    "wolf_relaxed2.png",
    "wolf_relaxed3.png",
    "wolf_relaxed2.png",
]


class Wolfi(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.wolfi.RAMMonitor")

        self.frames = []
        self.frame_index = 0
        self.image = None
        self.window = None

    def do_activate(self):
        # Load animation frames
        for filename in FRAMES:
            path = ASSETS_DIR / filename

            if not path.is_file():
                print(f"Missing image: {path}")
                return

            texture = Gdk.Texture.new_from_filename(str(path))
            self.frames.append(texture)

        self.image = Gtk.Picture()
        self.image.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.image.set_can_shrink(True)
        self.image.set_size_request(DOG_SIZE, DOG_SIZE)
        self.image.set_paintable(self.frames[0])

        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("Wolfi")
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.set_child(self.image)

        self.window.present()

        GLib.timeout_add(FRAME_INTERVAL_MS, self.advance_frame)

        print("Wolfi is running!")

    def advance_frame(self):
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.image.set_paintable(self.frames[self.frame_index])
        return GLib.SOURCE_CONTINUE

# Remove default widget backgrounds
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

app = Wolfi()
app.run()