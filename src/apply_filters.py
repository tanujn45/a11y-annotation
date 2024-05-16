from scipy.signal import butter, filtfilt
import numpy as np
import pdb


def butter_lowpass_filter(df, prefix="acc"):
    pdb.set_trace()
    fs = 50
    order = 1
    filter_type = "lowpass"
    nyq = 0.5 * fs
    cutoff = 10
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype=filter_type, analog=False)

    acc_x = df[prefix + "_x"]
    acc_y = df[prefix + "_y"]
    acc_z = df[prefix + "_z"]

    lp_x = filtfilt(b, a, acc_x)
    lp_y = filtfilt(b, a, acc_y)
    lp_z = filtfilt(b, a, acc_z)

    df[prefix + "_lp_x"] = lp_x
    df[prefix + "_lp_y"] = lp_y
    df[prefix + "_lp_z"] = lp_z

    return df


def moving_average(df, prefix="acc", rolling_window_size=2):
    df[prefix + "_ma_x"] = df[prefix + "_x"].rolling(rolling_window_size).mean()
    df[prefix + "_ma_y"] = df[prefix + "_y"].rolling(rolling_window_size).mean()
    df[prefix + "_ma_z"] = df[prefix + "_z"].rolling(rolling_window_size).mean()
    return df


def differentitaion(df, prefix="acc"):
    df[prefix + "_diff_x"] = df[prefix + "_x"].diff().dropna()
    df[prefix + "_diff_y"] = df[prefix + "_y"].diff().dropna()
    df[prefix + "_diff_z"] = df[prefix + "_z"].diff().dropna()
    return df
