import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# Structure to contain all our information, so we can pass it around
class CustomData:
    def __init__(self):
        self.playbin = None  # Our one and only element
        self.playing = False  # Are we in the PLAYING state?
        self.terminate = False  # Should we terminate execution?
        self.seek_enabled = False  # Is seeking enabled for this media?
        self.seek_done = False  # Have we performed the seek already?
        self.duration = Gst.CLOCK_TIME_NONE  # How long does this media last, in nanoseconds

# Forward definition of the message processing function
def handle_message(data, msg):
    if msg.type == Gst.MessageType.ERROR:
        err, debug_info = msg.parse_error()
        print("Error received from element {}: {}".format(msg.src.get_name(), err.message))
        print("Debugging information: {}".format(debug_info if debug_info else "none"))
        data.terminate = True
    elif msg.type == Gst.MessageType.EOS:
        print("\nEnd-Of-Stream reached.")
        data.terminate = True
    elif msg.type == Gst.MessageType.STATE_CHANGED:
        if msg.src == data.playbin:
            old_state, new_state, pending_state = msg.parse_state_changed()
            print("Pipeline state changed from {} to {}:".format(Gst.Element.state_get_name(old_state), Gst.Element.state_get_name(new_state)))

            # Remember whether we are in the PLAYING state or not
            data.playing = (new_state == Gst.State.PLAYING)

            if data.playing:
                # We just moved to PLAYING. Check if seeking is possible
                query = Gst.Query.new_seeking(Gst.Format.TIME)
                if data.playbin.query(query):
                    _, data.seek_enabled, start, end = query.parse_seeking()
                    if data.seek_enabled:
                        print("Seeking is ENABLED from {} to {}".format(Gst.TIME_ARGS_FORMAT(start), Gst.TIME_ARGS_FORMAT(end)))
                    else:
                        print("Seeking is DISABLED for this stream.")
                else:
                    print("Seeking query failed.")
    else:
        # We should not reach here
        print("Unexpected message received.")

    return True

def main():
    # Initialize GStreamer
    Gst.init(None)

    # Create the elements
    data = CustomData()
    data.playbin = Gst.ElementFactory.make("playbin", "playbin")
    if not data.playbin:
        print("Not all elements could be created.")
        return -1

    # Set the URI to play
    data.playbin.set_property("uri", "https://gstreamer.freedesktop.org/data/media/sintel_trailer-480p.webm")

    # Start playing
    ret = data.playbin.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("Unable to set the pipeline to the playing state.")
        return -1

    # Listen to the bus
    bus = data.playbin.get_bus()
    bus.add_signal_watch()
    bus.connect("message", handle_message, data)

    # Main loop
    try:
        while not data.terminate:
            msg = bus.timed_pop_filtered(100 * Gst.MSECOND, Gst.MessageType.STATE_CHANGED | Gst.MessageType.ERROR | Gst.MessageType.EOS)

            if msg:
                handle_message(data, msg)

            # Query the current position of the stream
            if data.playing:
                current = -1
                _, current = data.playbin.query_position(Gst.Format.TIME)

                if current < 0:
                    print("Could not query current position.")

                # If we didn't know it yet, query the stream duration
                if not Gst.CLOCK_TIME_IS_VALID(data.duration):
                    _, data.duration = data.playbin.query_duration(Gst.Format.TIME)

                    if not Gst.CLOCK_TIME_IS_VALID(data.duration):
                        print("Could not query current duration.")

                # Print current position and total duration
                print("Position {} / {}".format(Gst.TIME_ARGS_FORMAT(current), Gst.TIME_ARGS_FORMAT(data.duration)))

                # If seeking is enabled, we have not done it yet, and the time is right, seek
                if data.seek_enabled and not data.seek_done and current > 10 * Gst.SECOND:
                    print("\nReached 10s, performing seek...")
                    data.playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 30 * Gst.SECOND)
                    data.seek_done = True

    except KeyboardInterrupt:
        pass

    # Free resources
    data.playbin.set_state(Gst.State.NULL)
    data.playbin = None
    bus.remove_signal_watch()

if __name__ == "__main__":
    main()
