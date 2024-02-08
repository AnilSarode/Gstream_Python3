import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib

# Class to contain all our information, so we can pass it to callbacks
class CustomData:
    def __init__(self):
        self.pipeline = None
        self.source = None
        self.video_convert = None
        self.audio_convert = None
        self.video_sink = None
        self.audio_sink = None

# Handler for the pad-added signal
def pad_added_handler(src, new_pad, data):
    new_pad_type = new_pad.query_caps(None).to_string()
    print("Received new pad '{}' from '{}':".format(new_pad.get_name(), src.get_name()))

    if new_pad_type.startswith("audio/x-raw"):
        # If our audio convert is already linked, we have nothing to do here
        sink_pad = data.audio_convert.get_static_pad("sink")
    elif new_pad_type.startswith("video/x-raw"):
        # If our video convert is already linked, we have nothing to do here
        sink_pad = data.video_convert.get_static_pad("sink")
    else:
        print("Unknown pad type '{}'. Ignoring.".format(new_pad_type))
        return

    if sink_pad.is_linked():
        print("We are already linked. Ignoring.")
        return

    # Attempt the link
    ret = new_pad.link(sink_pad)
    if ret != Gst.PadLinkReturn.OK:
        print("Link failed.")
    else:
        print("Link succeeded.")

def main():
    # Initialize GStreamer
    Gst.init(None)

    # Create the elements
    data = CustomData()
    data.source = Gst.ElementFactory.make("uridecodebin", "source")
    data.video_convert = Gst.ElementFactory.make("videoconvert", "video_convert")
    data.audio_convert = Gst.ElementFactory.make("audioconvert", "audio_convert")
    data.video_sink = Gst.ElementFactory.make("autovideosink", "video_sink")
    data.audio_sink = Gst.ElementFactory.make("autoaudiosink", "audio_sink")

    # Create the empty pipeline
    data.pipeline = Gst.Pipeline.new("test-pipeline")

    if not data.pipeline or not data.source or not data.video_convert or not data.audio_convert or not data.video_sink or not data.audio_sink:
        print("Not all elements could be created.")
        return -1

    # Build the pipeline. Note that we are NOT linking the source at this point. We will do it later.
    data.pipeline.add(data.source)
    data.pipeline.add(data.video_convert)
    data.pipeline.add(data.audio_convert)
    data.pipeline.add(data.video_sink)
    data.pipeline.add(data.audio_sink)

    if not data.video_convert.link(data.video_sink) or not data.audio_convert.link(data.audio_sink):
        print("Elements could not be linked.")
        return -1

    # Set the URI to play
    data.source.set_property("uri", "https://gstreamer.freedesktop.org/data/media/sintel_trailer-480p.webm")

    # Connect to the pad-added signal
    data.source.connect("pad-added", pad_added_handler, data)

    # Start playing
    ret = data.pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("Unable to set the pipeline to the playing state.")
        return -1

    # Listen to the bus
    bus = data.pipeline.get_bus()
    terminate = False
    while not terminate:
        msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.STATE_CHANGED | Gst.MessageType.ERROR | Gst.MessageType.EOS)

        # Parse message
        if msg:
            if msg.type == Gst.MessageType.ERROR:
                err, debug_info = msg.parse_error()
                print("Error received from element {}: {}".format(msg.src.get_name(), err))
                print("Debugging information: {}".format(debug_info if debug_info else "none"))
                terminate = True
            elif msg.type == Gst.MessageType.EOS:
                print("End-Of-Stream reached.")
                terminate = True
            elif msg.type == Gst.MessageType.STATE_CHANGED:
                # We are only interested in state-changed messages from the pipeline
                if msg.src == data.pipeline:
                    old_state, new_state, pending_state = msg.parse_state_changed()
                    print("Pipeline state changed from {} to {}:".format(Gst.Element.state_get_name(old_state), Gst.Element.state_get_name(new_state)))
            else:
                # We should not reach here
                print("Unexpected message received.")

    # Free resources
    data.pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    main()
