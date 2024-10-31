import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

def tutorial_main():
    # Initialize GStreamer
    Gst.init(None)

    # Create the elements
    source = Gst.ElementFactory.make("videotestsrc", "source")
    sink = Gst.ElementFactory.make("autovideosink", "sink")

    # Create the empty pipeline
    pipeline = Gst.Pipeline.new("test-pipeline")
    print(pipeline, type(pipeline))
    if not pipeline or not source or not sink:
        print("Not all elements could be created.")
        return -1

    # Build the pipeline
    pipeline.add(source)
    pipeline.add(sink)
    if not source.link(sink):
        print("Elements could not be linked.")
        pipeline.unref()
        return -1

    # Modify the source's properties
    source.set_property("pattern", 0)

    # Start playing
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("Unable to set the pipeline to the playing state.")
        pipeline.unref()
        return -1

    # Wait until error or EOS
    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

    # Parse message
    if msg is not None:
        if msg.type == Gst.MessageType.ERROR:
            err, debug_info = msg.parse_error()
            print(f"Error received from element {msg.src.get_name()}: {err.message}")
            print(f"Debugging information: {debug_info if debug_info else 'none'}")
        elif msg.type == Gst.MessageType.EOS:
            print("End-Of-Stream reached.")
        else:
            print("Unexpected message received.")
        #msg.unref()

    # Free resources
    bus.unref()
    pipeline.set_state(Gst.State.NULL)
    pipeline.unref()
    return 0

def main():
    tutorial_main()

if __name__ == "__main__":
    main()
