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

    TTS.getText2VoiceStream("온도를 측정하고 있습니다.", file_name)
    MS.play_file(file_name)
    humi,temp = dht.read_retry(dht.DHT11, 3)

    TTS.getText2VoiceStream("온도와 습도 중에 원하는 센서값을 알려주세요.", file_name)
    MS.play_file(file_name)

    text = STT.getVoice2Text()

    if text.find("온도") >= 0:
        TTS.getText2VoiceStream("현재온도는 {}도 입니다.".format(temp), file_name)
        MS.play_file(file_name)
    elif text.find("습도") >= 0:
        TTS.getText2VoiceStream("현재습도는 {}퍼센트 입니다.".format(humi), file_name)
        MS.play_file(file_name)

if __name__ == '__main__':
    main()

