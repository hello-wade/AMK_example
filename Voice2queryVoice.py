#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Example 6: STT + Dialog - queryByVoice"""

from __future__ import print_function

import grpc

import gigagenieRPC_pb2
import gigagenieRPC_pb2_grpc

import os
import datetime
import hmac
import hashlib

# Config for GiGA Genie gRPC
CLIENT_ID = ''
CLIENT_KEY = ''
CLIENT_SECRET = ''
HOST = 'gate.gigagenie.ai'
PORT = 4080

### COMMON : Client Credentials ###
def getMetadata():
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    message = CLIENT_ID + ':' + timestamp

    signature = hmac.new(CLIENT_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()

    metadata = [('x-auth-clientkey', CLIENT_KEY),
                ('x-auth-timestamp', timestamp),
                ('x-auth-signature', signature)]

    return metadata

def credentials(context, callback):
    callback(getMetadata(), None)

def getCredentials():
    with open('../data/ca-bundle.pem', 'rb') as f:
        trusted_certs = f.read()
    sslCred = grpc.ssl_channel_credentials(root_certificates=trusted_certs)

    authCred = grpc.metadata_call_credentials(credentials)

    return grpc.composite_channel_credentials(sslCred, authCred)

### END OF COMMON ###

### STT
import pyaudio
import audioop
from six.moves import queue

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 512

# MicrophoneStream - original code in https://goo.gl/7Xy3TT
class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)
# [END audio_stream]

import wave

def play_file(fname):
    # create an audio object
    wf = wave.open(fname, 'rb')
    p = pyaudio.PyAudio()
    chunk = 1024

    # open stream based on the wave object which has been input.
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # read data (based on the chunk size)
    data = wf.readframes(chunk)

    # play stream (looping from beginning of file to the end)
    while len(data) > 0:
        # writing to the stream is what *actually* plays the sound.
        stream.write(data)
        data = wf.readframes(chunk)

        # cleanup stuff.
    stream.close()
    p.terminate()

# KWS

import ktkws
KWSID = ['기가지니', '지니야', '친구야', '자기야']

def detect():

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()

        for content in audio_generator:

            rc = ktkws.detect(content)
            rms = audioop.rms(content,2)
            print('audio rms = %d' % (rms))

            if (rc == 1):
                play_file("../data/sample_sound.wav")
                return 200

def test():
    rc = ktkws.init("../data/kwsmodel.pack")
    print ('init rc = %d' % (rc))
    rc = ktkws.start()
    print ('start rc = %d' % (rc))
    ktkws.set_keyword(KWSID.index('기가지니'))
    rc = detect()
    print ('detect rc = %d' % (rc))
    ktkws.stop()
    return rc

def getText2VoiceStream(inText,inFileName):

    channel = grpc.secure_channel('{}:{}'.format(HOST, PORT), getCredentials())
    stub = gigagenieRPC_pb2_grpc.GigagenieStub(channel)

    message = gigagenieRPC_pb2.reqText()
    message.lang=0
    message.mode=0
    message.text=inText
    writeFile=open(inFileName,'wb')
    for response in stub.getText2VoiceStream(message):
        if response.HasField("resOptions"):
            print ("ResVoiceResult: %d" %(response.resOptions.resultCd))
        if response.HasField("audioContent"):
            print ("Audio Stream")
            writeFile.write(response.audioContent)
    writeFile.close()

def print_rms(rms):
    out = ''
    for _ in range(int(round(rms/30))):
        out = out + '*'

    print (out)

def generate_request():
    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        messageReq = gigagenieRPC_pb2.reqQueryVoice()
        messageReq.reqOptions.lang=0
        messageReq.reqOptions.userSession="1234"
        messageReq.reqOptions.deviceId="aklsjdnalksd"
        yield messageReq
        for content in audio_generator:
            message = gigagenieRPC_pb2.reqQueryVoice()
            message.audioContent = content
            yield message
            rms = audioop.rms(content,2)
            print_rms(rms)

def queryByVoice():
    print ("Ctrl+\ to quit ...")
    channel = grpc.secure_channel('{}:{}'.format(HOST, PORT), getCredentials())
    stub = gigagenieRPC_pb2_grpc.GigagenieStub(channel)
    request = generate_request()
    resultText = ''
    response = stub.queryByVoice(request)
    print ("resultCd: %d" % (response.resultCd))
    if response.resultCd == 200:
        print ("uword: %s" % (response.uword))
        for a in response.action:
            resultText = a.mesg
            print (a.mesg)
            print (a.actType)

    else:
        print ("Fail: %d" % (response.resultCd))
    return resultText

def main():
    query_start = test()
    print(query_start)
    if query_start == 200 :
        return_text = queryByVoice()
        print("return : ", return_text)
        file_name = "./testtts.wav"
        return_test = getText2VoiceStream(return_text,file_name)
        print("return test", return_test)
        play_file(file_name)


if __name__ == '__main__':
    main()
