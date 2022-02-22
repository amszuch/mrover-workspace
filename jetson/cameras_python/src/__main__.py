from rover_common.aiohelper import run_coroutines
from rover_common import aiolcm
import asyncio
from rover_msgs import Cameras
import gi
import time
gi.require_version("Gst", "1.0")
from gi.repository import Gst # noqa

lcm_ = aiolcm.AsyncLCM()
pipeline = [None, None, None, None, None, None, None, None]
streaming = [False, False, False, False, False, False, False, False]
video_names = [0, 1, 2, 3, 4, 5, 6, 7]
ports = [0, 1, 3, 4, 5, 6, 7, 8]
last_time = time.process_time()


def start_pipeline(index):
    global pipeline
    pipeline_string = ("v4l2src device=/dev/video" + str(video_names[index]) + " ! "
                       "videoscale ! videoconvert ! x264enc tune=zerolatency "
                       "bitrate=500 speed-preset=superfast ! rtph264pay ! "
                       "udpsink host=10.0.0.1 port=500" + str(ports[index]))

    if pipeline[index] is None:
        pipeline[index] = Gst.parse_launch(pipeline_string)

    print("Playing camera " + str(index) + " pipeline.")


def stop_pipeline(index):
    global pipeline

    pipeline[index].set_state(Gst.State.PAUSED)
    print("Stopping camera " + str(index) + " pipeline.")


def camera_callback(channel, msg):
    global pipeline
    global streaming

    camera_cmd = Cameras.decode(msg)

    requests_array = [camera_cmd.cam1, camera_cmd.cam2, camera_cmd.cam3, camera_cmd.cam4,
                      camera_cmd.cam5, camera_cmd.cam6, camera_cmd.cam7, camera_cmd.cam8]

    for i in range(len(requests_array)):
        if streaming[i] == requests_array[i]:
            continue
        streaming[i] = requests_array[i]
        if streaming[i]:
            start_pipeline(i)
        else:
            stop_pipeline(i)


async def refresh_cameras():

    while True:
        global last_time
        current_time = time.process_time()
        elapsed_time = current_time - last_time
        print(elapsed_time)
        if elapsed_time >= 8:
            last_time = time.process_time()
            global streaming
            global pipeline
            print("restart timers")
            for i in range(len(pipeline)):
                if streaming[i]:
                    stop_pipeline(i)
                    start_pipeline(i)

        await asyncio.sleep(0.5)


def main():
    Gst.init(None)
    lcm_.subscribe("/cameras_cmd", camera_callback)

    run_coroutines(lcm_.loop(), refresh_cameras())


if __name__ == "__main__":
    main()
