import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib

# Initialize Gstreamer
Gst.init(None)

# Create a Gstreamer pipeline
pipeline = Gst.Pipeline()

# Create elements for the pipeline
source = Gst.ElementFactory.make("v4l2src", "source")
source.set_property("device", "/dev/video1")  # Set the device to your UVC Camera
capsfilter = Gst.ElementFactory.make("capsfilter", "capsfilter")
caps = Gst.Caps.from_string("video/x-raw, width=640, height=480")  # Adjust width and height as needed
capsfilter.set_property("caps", caps)
sink = Gst.ElementFactory.make("autovideosink", "sink")

# Add elements to the pipeline
pipeline.add(source)
pipeline.add(capsfilter)
pipeline.add(sink)

# Link elements
source.link(capsfilter)
capsfilter.link(sink)

# Set the pipeline state to playing
pipeline.set_state(Gst.State.PLAYING)

# Create a main loop to handle Gstreamer events
loop = GLib.MainLoop()

try:
    loop.run()
except KeyboardInterrupt:
    # Stop the pipeline when the user interrupts the program
    pipeline.set_state(Gst.State.NULL)
    loop.quit()
