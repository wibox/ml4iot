import scipy.io.wavfile as siw
import sounddevice as sd
import time as t
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--resolution", type=str, default="int32")
parser.add_argument("--sr", type=int, default=48000)

args = parser.parse_args()

print("Start recording...")

store_audio = True

def callback(indata, frames, callback_time, status):
    global store_audio
    #indata = inputdata
    #frames = numero di elementi contenuti in questa chiamata della callback
    if store_audio:
        timestamp = t.time()
        siw.write(filename=f"recordings/{timestamp}.wav", rate=48000, data=indata)
        #Nbits/sample = 32
        #size = samples/second * duration in s * nBits/sample = 48000 * 1 * 32 / 8
        sizeBytes = os.path.getsize(f"recordings/{timestamp}.wav")
        sizeKB = sizeBytes / 1024.
        print(f"Size in KB: {sizeKB}")

with sd.InputStream(device=0, channels=1, samplerate=48000, dtype=args.resolution, callback=callback, blocksize=48000):
    #device=0 singolo microfono di default
    #channels=1 per indicare quanti microfoni del sensore audio vengono usati
    #samplerate numbero di sample presi al secondo -> (Hz)
    #dtype indica quanta memoria viene usata per il singolo sample
    #callback indica la funzione di callback da chiamare
    #blocksize indica ogni quanti sample viene chiamata callback(). 48000 -> ogni secondo per design
    while True:
        key = input()
        if key in ["Q", "q"]:
            print("Stopping recording.")
            break
        if key in ["P", "p"]:
            print("Stopped storing audio on the filesystem")
            store_audio = not store_audio