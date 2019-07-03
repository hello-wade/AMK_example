#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Example 2: STT - getVoice2Text """

from __future__ import print_function

import time
import MicrophoneStream as MS
import ex1_kwstest as kws
import ex2_getVoice2Text as STT
import ex4_getText2VoiceStream as TTS

import RPi.GPIO as GPIO

def main():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(31, GPIO.OUT)
    output_file = "testtts.wav"

    text = STT.getVoice2Text()

    if text.find("불 켜") >=0:
        GPIO.output(31, GPIO.HIGH)
        TTS.getText2VoiceStream("불을 켭니다.", output_file)
        MS.play_file(output_file)

    elif text.find("불 꺼") >=0:
        GPIO.output(31, GPIO.LOW)
        TTS.getText2VoiceStream("불을 끕니다.", output_file)
        MS.play_file(output_file)


if __name__ == '__main__':
    main()
