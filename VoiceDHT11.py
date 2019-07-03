#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Example 2: STT - getVoice2Text """

import time
import MicrophoneStream as MS
import ex1_kwstest as kws
import ex2_getVoice2Text as STT
import ex4_getText2VoiceStream as TTS

import Adafruit_DHT as dht


def main():
    file_name = "./testtts.wav"

    humi, temp = dht.read_retry(dht.DHT11, 2)
    text = STT.getVoice2Text()

    if text.find("온도") >= 0:
        temp_str = TTS.getText2VoiceStream("현재온도는 {}도 입니다.".format(temp), file_name)
        MS.play_file(file_name)
    elif text.find("습도") >= 0:
        humi_str = TTS.getText2VoiceStream("현재습도는 {}퍼센트 입니다.".format(humi), file_name)
        MS.play_file(file_name)

if __name__ == '__main__':
    main()
