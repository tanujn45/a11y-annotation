import subprocess
import pandas as pd
import os
import cv2
from src.apply_filters import butter_lowpass_filter, moving_average, differentitaion

data_path = "/Users/tanujnamdeo/Desktop/AAC/annotation/src/data/"
raw_csv_path = data_path + "raw_csv/"
trimmed_csv_path = data_path + "trimmed_csv/"
raw_video_path = data_path + "raw_video/"
trimmed_video_path = data_path + "trimmed_video/"

frequency = 50


def run(cmd):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        encoding="utf-8",
        errors="replace",
    )

    while True:
        realtime_output = process.stdout.readline()

        if realtime_output == "" and process.poll() is not None:
            break

        if realtime_output:
            print(realtime_output.strip(), flush=True)

    return process


def create_directory_if_not_exists(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def store_in_master_csv(filename, gesture_name, start_time, end_time, duration):
    file_path = os.path.join(data_path, "master.csv")

    if not os.path.exists(file_path):
        df = pd.DataFrame(
            columns=[
                "Filename",
                "Video duration",
                "Gesture name",
                "Start time",
                "End time",
                "Gesture duration",
            ]
        )
        df.to_csv(file_path, index=False)

    df = pd.read_csv(file_path)
    new_gesture_entry = {
        "Filename": filename,
        "Video duration": round(duration, 2),
        "Gesture name": gesture_name,
        "Start time": start_time,
        "End time": end_time,
        "Gesture duration": round(end_time - start_time, 2),
    }

    if df[(df["Filename"] == filename) & (df["Gesture name"] == gesture_name)].empty:
        df = pd.concat([df, pd.DataFrame([new_gesture_entry])], ignore_index=True)
        df.to_csv(file_path, index=False)


def apply_filters_to_csv(trimmed_curr_csv_path):

    df = pd.read_csv(trimmed_curr_csv_path)
    df = differentitaion(df, "acc")
    df.to_csv(trimmed_curr_csv_path, index=False)
    df = moving_average(df, "acc")
    df.to_csv(trimmed_curr_csv_path, index=False)
    df = butter_lowpass_filter(df, "acc")
    df.to_csv(trimmed_curr_csv_path, index=False)


def create_trimmed_csv(filename, gesture_name, start_time, end_time):
    trimmed_filename = gesture_name.replace(" ", "_").lower() + ".csv"
    trimmed_curr_csv_path = os.path.join(trimmed_csv_path, trimmed_filename)

    raw_curr_csv_path = os.path.join(raw_csv_path, filename + ".csv")
    df = pd.read_csv(raw_curr_csv_path)

    if "Id" not in df.columns:
        df["Id"] = range(len(df))
    if "Time" not in df.columns:
        df["Time"] = df["Id"] / frequency

    df = differentitaion(df)
    df = moving_average(df)
    # df = butter_lowpass_filter(df)

    df = df[(df["Time"] >= start_time) & (df["Time"] <= end_time)]

    df.to_csv(trimmed_curr_csv_path, index=False)
    return trimmed_curr_csv_path


def create_trimmed_video(video_name, gesture_name, start_time, end_time):
    trimmed_filename = gesture_name.replace(" ", "_").lower() + ".mp4"
    trimmed_curr_video_path = os.path.join(trimmed_video_path, trimmed_filename)

    raw_curr_video_path = os.path.join(raw_video_path, video_name + ".mp4")
    video_duration = get_video_length(raw_curr_video_path)

    if end_time > video_duration:
        end_time = video_duration

    cmd = f"ffmpeg -i {raw_curr_video_path} -ss {start_time} -to {end_time} -avoid_negative_ts make_zero {trimmed_curr_video_path}"
    # cmd = f"ffmpeg -i {raw_curr_video_path} -ss {start_time} -to {end_time} -c:v libx264 -preset ultrafast -crf 0 {trimmed_curr_video_path}"
    run(cmd)

    return trimmed_filename


def get_video_length(video_file_path):
    cap = cv2.VideoCapture(video_file_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    video_length = frame_count / fps
    cap.release()
    return video_length


def trim(video_name, start_time=0, end_time=None, gesture_name=""):
    create_directory_if_not_exists(trimmed_csv_path)
    create_directory_if_not_exists(trimmed_video_path)

    video_duration = get_video_length(video_name)
    if not end_time:
        end_time = video_duration

    video_name = video_name.split("/")[-1].split(".")[0]

    # Make an entry in the Master CSV
    store_in_master_csv(video_name, gesture_name, start_time, end_time, video_duration)
    new_file = create_trimmed_csv(video_name, gesture_name, start_time, end_time)

    trimmed_gesture_name = create_trimmed_video(
        video_name, gesture_name, start_time, end_time
    )

    return trimmed_gesture_name
