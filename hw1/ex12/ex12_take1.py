import numpy as np
import tensorflow as tf
import scipy.io.wavfile as siw
import sounddevice as sd
import time as t
import os
import argparse

from preprocessing import *

parser = argparse.ArgumentParser()
parser.add_argument("--resolution", type = str, default = "int16")
parser.add_argument("--sampling-rate", type = int, default = 16000)
parser.add_argument("--num-channels", type = int, default = 1)
parser.add_argument("--block_size", type = int, default = 16000)
parser.add_argument("--device", type=int, default=1)
args = parser.parse_args()

print("Recording...")
def callback(indata, frames, callback_time, status):
    #mydata = np.array(indata[1], dtype=float)
    mydata = get_audio_from_numpy(indata)
    if not is_silence(npdata=mydata, downsampling_rate=16000, frame_length_in_s=0.4, dbFSthresh=-200, duration_time=0.01, sampling_rate= args.sampling_rate):
        print("saving_audio")
        timestamp = t.time()
        siw.write(filename=f"recordings/{timestamp}.wav", rate=args.sampling_rate, data=indata)


def is_silence(npdata, downsampling_rate, frame_length_in_s, dbFSthresh, duration_time, sampling_rate):
    #audio = get_audio_from_numpy(npdata)
    #print(type(audio))
    spectrogram, _ = get_spectrogram(
        npdata,
        downsampling_rate,
        frame_length_in_s,
        frame_length_in_s,
        sampling_rate
    )
    dbFS = 20 * tf.math.log(spectrogram + 1.e-6)
    energy = tf.math.reduce_mean(dbFS, axis=1)
    non_silence = energy > dbFSthresh
    non_silence_frames = tf.math.reduce_sum(tf.cast(non_silence, tf.float32))
    non_silence_duration = (non_silence_frames + 1) * frame_length_in_s

    if non_silence_duration > duration_time:
        return 0
    else:
        return 1

with sd.InputStream(device=args.device, channels=args.num_channels, samplerate=args.sampling_rate, dtype=args.resolution, callback=callback, blocksize=args.block_size):
    while True:
        key = input()
        if key in ["Q", "q"]:
            print("Stopping recording.")
            break