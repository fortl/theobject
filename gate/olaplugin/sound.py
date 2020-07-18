import pyaudio
import numpy as np

CHUNK = 2*2048 # number of data points to read at a time
RATE = 44100 # time resolution of the recording device (Hz)
TIME_INTERVAL = CHUNK/RATE
TIMELINE_LEN = 30

DEVICE = 0 # default
SLICES_COUNT = 5
S_SHIFT = 10
S_LEN = int((CHUNK/2)/SLICES_COUNT) 

FADING = 0.2

data_handler = None
timeline = [[0 for i in range(SLICES_COUNT)] for j in range(TIMELINE_LEN)]
average = [0]*SLICES_COUNT

def blocking_analize():
    global timeline, average
    p = pyaudio.PyAudio()

    stream=p.open(format=pyaudio.paInt16,channels=1,rate=RATE,input=True, input_device_index=DEVICE,
                frames_per_buffer=CHUNK)

    while True:
        indata = np.frombuffer(stream.read(CHUNK, exception_on_overflow = False),dtype=np.int16)/2**15
        indata = indata-np.average(indata)
        fftData = np.abs(np.fft.rfft(indata))
        maxVolume = np.max(fftData[S_SHIFT:])
        # which = fftData[MIN_FREQ:].argmax() + MIN_FREQ
        # print(maxVolume)
        intervals = [
            np.max(fftData[S_SHIFT+i+S_LEN*i:S_SHIFT+i+S_LEN*(i+1)-1])
                for i in range(SLICES_COUNT)]
        timeline.pop(-1)
        timeline.insert(1, intervals)
        average=[(av + x*FADING)/(FADING+1) for (av, x) in zip(average, intervals)]
   
        if data_handler:
            data_handler(timeline, average)

    stream.close()
    p.terminate()

def start_analize(handler):
    global data_handler
    data_handler = handler
    return blocking_analize
