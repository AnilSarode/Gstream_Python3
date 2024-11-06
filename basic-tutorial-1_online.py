import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

def tutorial_main(uri):
    # Initialize GStreamer
    Gst.init(None)

    # Build the pipeline with the specified URI
    pipeline = Gst.parse_launch(f"playbin uri={uri}")

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
    # Specify the URL of the video to play
    video_url = "https://home/anil/Downloads/videoplayback.webm"
    tutorial_main(video_url)

if __name__ == "__main__":
    main()
