import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

def tutorial_main():
    # Initialize GStreamer
    Gst.init(None)

    # Build the pipeline
    pipeline = Gst.parse_launch("playbin uri=https://gstreamer.freedesktop.org/data/media/sintel_trailer-480p.webm")

    # Start playing
    pipeline.set_state(Gst.State.PLAYING)

    # Wait until error or EOS
    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

    # See next tutorial for proper error message handling/parsing
    if msg.type == Gst.MessageType.ERROR:
        error, _ = msg.parse_error()
        print("Error occurred:", error)
    
    # Free resources
    pipeline.set_state(Gst.State.NULL)

def main():
    tutorial_main()

if __name__ == "__main__":
    main()
