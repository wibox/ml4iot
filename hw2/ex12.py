import psutil
from time import time, sleep
from datetime import datetime
import uuid
import redis
from time import time
import argparse
import sounddevice as sd
import tensorflow as tf
import tensorflow_io as tfio
import scipy.io.wavfile as siw
import os
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--host", type = str, default = "redis-15072.c77.eu-west-1-1.ec2.cloud.redislabs.com")
parser.add_argument("--port", type = int, default = 15072)
parser.add_argument("--user", type = str, default = "default")
parser.add_argument("--password", type = str, default = "53R8YAlL81zAHIEVcPjwjzcnVQoSPhzt")
parser.add_argument("--device", type = int, default = 1)  #### rivedere questo
args = parser.parse_args()

def safe_ts_create(redis_client, key):
    try:
        redis_client.ts().create(key)
    except redis.ResponseError:
        pass

def get_audio_from_numpy(indata):
    indata = tf.convert_to_tensor(indata, dtype=tf.float32)
    indata = 2 * ((indata + 32768) / (32767 + 32768)) - 1 
    indata = tf.squeeze(indata)
    return indata

def get_spectrogram(
    nparray,
    downsampling_rate, 
    frame_length_in_s, 
    frame_step_in_s,
    sampling_rate): 

    audio_padded = get_audio_from_numpy(nparray)

    if sampling_rate != downsampling_rate:
        sampling_rate_int64 = tf.cast(sampling_rate, tf.int64)
        audio_padded = tfio.audio.resample(audio_padded, sampling_rate_int64, downsampling_rate)

    sampling_rate_float32 = tf.cast(sampling_rate, tf.float32)
    frame_length = int(frame_length_in_s*sampling_rate_float32)
    frame_step = int(frame_step_in_s*sampling_rate_float32)

    #building the spectrogram
    stft = tf.signal.stft(
        audio_padded,
        frame_length = frame_length,
        frame_step = frame_step,
        fft_length = frame_length
    )

    spectrogram = tf.abs(stft)

    return spectrogram, sampling_rate

def callback(indata, frames, callback_time, status):
        #mydata = np.array(indata[1], dtype=float)
        mydata = get_audio_from_numpy(indata)
        if not is_silence(npdata=mydata, downsampling_rate=16000, frame_length_in_s=0.5, dbFSthresh=-105, duration_time=0.5, sampling_rate= 16000):
            print("saving_audio")
            timestamp = time()
            siw.write(filename=f"recordings/{timestamp}.wav", rate=16000, data=indata)


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

def go_stop_classification(
    filename, 
    downsampling_rate, 
    frame_length,
    frame_step,
    linear_to_mel_weight_matrix,
    interpreter,
    input_details,
    output_details,
    LABELS = ["go","stop"]):

    #filename = f"recordings/{tmp}.wav"
    audio_binary = tf.io.read_file(filename)
    # path_parts = tf.strings.split(filename, '/')
    # path_end = path_parts[-1]
    # file_parts = tf.strings.split(path_end, '_')
    # true_label = file_parts[0]
    # true_label = true_label.numpy().decode()
    
    audio, sampling_rate = tf.audio.decode_wav(audio_binary) 
    audio = tf.squeeze(audio)
    zero_padding = tf.zeros(sampling_rate - tf.shape(audio), dtype=tf.float32)
    audio_padded = tf.concat([audio, zero_padding], axis=0)

    if downsampling_rate != sampling_rate:
        audio_padded = tfio.audio.resample(audio_padded, tf.cast(downsampling_rate, tf.int64), downsampling_rate)

    stft = tf.signal.stft(
        audio_padded, 
        frame_length=frame_length,
        frame_step=frame_step,
        fft_length=frame_length
    )
    spectrogram = tf.abs(stft)
    mel_spectrogram = tf.matmul(spectrogram, linear_to_mel_weight_matrix)
    log_mel_spectrogram = tf.math.log(mel_spectrogram + 1.e-6)
    log_mel_spectrogram = tf.expand_dims(log_mel_spectrogram, 0)
    log_mel_spectrogram = tf.expand_dims(log_mel_spectrogram, -1)
    log_mel_spectrogram = tf.image.resize(log_mel_spectrogram, [32, 32])
    
    interpreter.set_tensor(input_details[0]['index'], log_mel_spectrogram) 
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])

    if output[0] > 0.95:
        top_index = np.argmax(output[0])
        predicted_label = LABELS[top_index]
    else:
        predicted_label = None
    
    return predicted_label


def main():
    redis_client = redis.Redis(
        host = args.host, 
        password = args.password, 
        username = args.user, 
        port = args.port)

    monitoring = False

    print("Is connected? ", redis_client.ping())

    ts_in_s = time()
    ts_in_ms = int(ts_in_s*1000)
    mac_id = hex(uuid.getnode())
    battery_level = psutil.sensors_battery().percent
    power_plugged = psutil.sensors_battery().power_plugged
    formatted_datetime = datetime.fromtimestamp(ts_in_s)
    print(f"{formatted_datetime} - {mac_id}: battery level ", battery_level)
    print(f"{formatted_datetime} - {mac_id}: power plugged: ", power_plugged)
    
    safe_ts_create(redis_client, "mac_adress:battery")
    safe_ts_create(redis_client, "mac_adress:power")

    flag = ""

    MODEL_NAME = 1670336541 #### NOME A OCCHIO
    interpreter = tf.lite.Interpreter(model_path=f'tflite_models/{MODEL_NAME}.tflite')
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # DA AUTOMATIZZARE
    downsampling_rate = 16000
    sampling_rate_int64 = tf.cast(downsampling_rate, tf.int64)
    frame_length = int(downsampling_rate * 0.04)
    frame_step = int(downsampling_rate * 0.02)
    spectrogram_width = (16000 - frame_length) // frame_step + 1
    num_spectrogram_bins = frame_length // 2 + 1

    linear_to_mel_weight_matrix = tf.signal.linear_to_mel_weight_matrix(
        num_mel_bins = 40,
        num_spectrogram_bins = num_spectrogram_bins,
        downsampling_rate = downsampling_rate,
        lower_frequency = 20,
        upper_frequency = 4000
    )

    # FINO QUA #######


    with sd.InputStream(device=args.device, channels=1, samplerate=16000, dtype="int16", callback=callback, blocksize=16000):
        while True:
            tmp = time()
            if os.path.exists(f"recordings/{tmp}.wav"):

                predicted_label = go_stop_classification(
                    f"recordings/{tmp}.wav", 
                    downsampling_rate, 
                    frame_length,
                    frame_step,
                    linear_to_mel_weight_matrix,
                    interpreter,
                    input_details,
                    output_details,
                    LABELS = ["go","stop"])

                if predicted_label == "go":
                    monitoring = True
                elif predicted_label == "stop":
                    monitoring = False 
                elif predicted_label == None:
                    continue
            
            if monitoring:
                redis_client.ts().add("mac_adress:battery", ts_in_ms, battery_level)
                redis_client.ts().add("mac_adress:power",ts_in_ms, int(power_plugged))

            sleep(1)

if __name__ == "__main__":
    main()