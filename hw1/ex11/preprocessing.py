import tensorflow as tf
import tensorflow_io as tfio

def get_audio_and_label(filename: str):
    audio_binary = tf.io.read_file(filename)
    audio, sampling_rate = tf.audio.decode_wav(audio_binary)
    label = filename.split("/")[1].split("_")[0]
    #label = fields[0]
    audio = tf.squeeze(audio)
    zero_padding = tf.zeros(sampling_rate-tf.shape(audio), dtype = tf.float32)
    audio_padded = tf.concat([audio, zero_padding], axis = 0)
    return audio, sampling_rate, label

def get_spectrogram(
    filename,
    downsampling_rate, 
    frame_length_in_s, 
    frame_step_in_s): 
    
    # come cristo si fa il downsampling (hp m/n * sampling_rate)

    #audio_binary = tf.io.read_file(filename)
    #_, sampling_rate = tf.audio.decode_wav(audio_binary)
    
    #spectr = tfio.audio.spectrogram(audio_binary, nfft = frame_length_in_s, window = frame_length_in_s, stride=frame_step_in_s)
        
    #downsampling_rate = sampling_rate
    #fields = tf.strings.split(filename, "_")
    #label = fields[0]

    #getting audio
    #audio_binary = tf.io.read_file(filename)
    #audio, sampling_rate = tf.audio.decode_wav(audio_binary)

    #padding dell'audio
    #zero_padding = tf.zeros(tf.shape(audio))
    #audio_padded = tf.concat([audio, zero_padding], axis=0)

    audio_padded, sampling_rate, label = get_audio_and_label(filename)

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

    return spectrogram, sampling_rate, label
    
def get_log_mel_spectrogram(
    filename,
    downsampling_rate, 
    frame_length_in_s, 
    frame_step_in_s,
    num_mel_bins,
    lower_frequency,
    upper_frequency):
    
    # downsampling rate occhio

    spectrogram, _, label = get_spectrogram(
        filename,
        downsampling_rate=downsampling_rate,
        frame_length_in_s=frame_length_in_s,
        frame_step_in_s=frame_step_in_s
        )
    
    linear_to_mel_weight_matrix = tf.signal.linear_to_mel_weight_matrix(
        num_mel_bins=num_mel_bins,
        num_spectrogram_bins = spectrogram.reshape[1],
        sampling_rate=downsampling_rate,
        lower_frequency=lower_frequency,
        upper_frequency=upper_frequency
    )

    mel_spectrogram = tf.matmul(spectrogram, linear_to_mel_weight_matrix)
    log_mel_spectrogram = tf.math.log(mel_spectrogram + 1e-6)
    
    return log_mel_spectrogram, label

def get_mfccs(
    filename,
    downsampling_rate, 
    frame_length_in_s, 
    frame_step_in_s,
    num_mel_bins,
    lower_frequency,
    upper_frequency,
    num_coefficients):

    
    return tf.signal.mfccs_from_log_mel_spectrograms(
                get_log_mel_spectrogram(
                    filename=filename,
                    downsampling_rate=downsampling_rate,
                    frame_length_in_s=frame_length_in_s,
                    frame_step_in_s=frame_step_in_s,
                    num_mel_bins=num_mel_bins,
                    lower_frequency=lower_frequency,
                    upper_frequency=upper_frequency
                )
            )

    
