#include <gst/gst.h>

typedef struct _CustomData {
  GstElement *pipeline;
  GstElement *video_source;
  GstElement *audio_source;
  GstElement *video_convert;
  GstElement *audio_convert;
  GstElement *video_sink;
  GstElement *audio_sink;
} CustomData;

int main(int argc, char *argv[]) {
  CustomData data;
  GstBus *bus;
  GstMessage *msg;
  GstStateChangeReturn ret;
  gboolean terminate = FALSE;

  gst_init (&argc, &argv);

  // Video elements
  data.video_source = gst_element_factory_make ("v4l2src", "video_source");
  data.video_convert = gst_element_factory_make ("videoconvert", "video_convert");
  data.video_sink = gst_element_factory_make ("autovideosink", "video_sink");

  // Audio elements
  data.audio_source = gst_element_factory_make ("alsasrc", "audio_source");
  data.audio_convert = gst_element_factory_make ("audioconvert", "audio_convert");
  data.audio_sink = gst_element_factory_make ("autoaudiosink", "audio_sink");

  // Create pipeline
  data.pipeline = gst_pipeline_new ("test-pipeline");

  if (!data.pipeline || !data.video_source || !data.video_convert || !data.video_sink || 
      !data.audio_source || !data.audio_convert || !data.audio_sink) {
    g_printerr ("Not all elements could be created.\n");
    return -1;
  }

  // Set device properties
  g_object_set (data.video_source, "device", "/dev/video0", NULL);
  g_object_set(data.audio_source, "device", "hw:1,0", NULL); // Adjust to your audio device if necessary

  // Build pipeline
  gst_bin_add_many (GST_BIN (data.pipeline), 
                    data.video_source, data.video_convert, data.video_sink,
                    data.audio_source, data.audio_convert, data.audio_sink, NULL);

  // Link video elements
  if (!gst_element_link_many (data.video_source, data.video_convert, data.video_sink, NULL)) {
    g_printerr ("Video elements could not be linked.\n");
    gst_object_unref (data.pipeline);
    return -1;
  }

  // Link audio elements
  if (!gst_element_link_many (data.audio_source, data.audio_convert, data.audio_sink, NULL)) {
    g_printerr ("Audio elements could not be linked.\n");
    gst_object_unref (data.pipeline);
    return -1;
  }

  // Start playing
  ret = gst_element_set_state (data.pipeline, GST_STATE_PLAYING);
  if (ret == GST_STATE_CHANGE_FAILURE) {
    g_printerr ("Unable to set the pipeline to the playing state.\n");
    gst_object_unref (data.pipeline);
    return -1;
  }

  // Listen to the bus
  bus = gst_element_get_bus (data.pipeline);
  do {
    msg = gst_bus_timed_pop_filtered (bus, GST_CLOCK_TIME_NONE,
                                      GST_MESSAGE_STATE_CHANGED | GST_MESSAGE_ERROR | GST_MESSAGE_EOS);

    if (msg != NULL) {
      GError *err;
      gchar *debug_info;

      switch (GST_MESSAGE_TYPE (msg)) {
        case GST_MESSAGE_ERROR:
          gst_message_parse_error (msg, &err, &debug_info);
          g_printerr ("Error received from element %s: %s\n", GST_OBJECT_NAME (msg->src), err->message);
          g_printerr ("Debugging information: %s\n", debug_info ? debug_info : "none");
          g_clear_error (&err);
          g_free (debug_info);
          terminate = TRUE;
          break;
        case GST_MESSAGE_EOS:
          g_print ("End-Of-Stream reached.\n");
          terminate = TRUE;
          break;
        case GST_MESSAGE_STATE_CHANGED:
          if (GST_MESSAGE_SRC (msg) == GST_OBJECT (data.pipeline)) {
            GstState old_state, new_state, pending_state;
            gst_message_parse_state_changed (msg, &old_state, &new_state, &pending_state);
            g_print ("Pipeline state changed from %s to %s:\n",
                     gst_element_state_get_name (old_state), gst_element_state_get_name (new_state));
          }
          break;
        default:
          g_printerr ("Unexpected message received.\n");
          break;
      }
      gst_message_unref (msg);
    }
  } while (!terminate);

  // Free resources
  gst_object_unref (bus);
  gst_element_set_state (data.pipeline, GST_STATE_NULL);
  gst_object_unref (data.pipeline);
  return 0;
}
