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
parser.add_argument("--device", type=int, default=0)
args = parser.parse_args()

print("Recording...")

def get_audio_from_numpy(indata):
    indata = tf.convert_to_tensor(indata, dtype=tf.float32)
    indata = (indata + 32768) / (32767 + 32768)
    indata = tf.squeeze(indata)
    return indata

def callback(indata, frames, callback_time, status):
    mydata = np.array(indata[1], dtype=float)
    if is_silence(npdata=mydata, downsampling_rate=16000, frame_length_in_s=0.4, dbFSthresh=-100, duration_time=0.01):
        timestamp = t.time()
        siw.write(filename=f"recordings/{timestamp}.wav", rate=args.sampling_rate, data=indata)

def is_silence(npdata, downsampling_rate, frame_length_in_s, dbFSthresh, duration_time):
    audio, _, _ = get_audio_from_numpy(npdata)
    spectrogram, _, _ = get_spectrogram(
        npdata,
        downsampling_rate,
        frame_length_in_s,
        frame_length_in_s
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

with sd.InputStream(device=args.device, channels=args.num_channels, samplerate=args.sampling_rate, dtype=args.resolution, callback=callback, blocksize=args.blocksize):
    while True:
        key = input()
        if key in ["Q", "q"]:
            print("Stopping recording.")
            break

