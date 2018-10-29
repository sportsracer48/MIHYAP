#!/usr/bin/python3
#prereqs:
#pygame-1.9.4 (pip3 install pygame)
#numpy-1.15.3 (pip3 install numpy)

import pygame
import numpy as np
import time
from gtts import gTTS
import subprocess
import random
import os
import RPi.GPIO as GPIO

def clock():
    return time.time()

WIDTH = 1920
HEIGHT = 1080

white = np.array([255,255,255])
black = np.array([0,0,0])
red   = np.array([255,0,0])

bgColor = white;
fgColor = black;

colorChanged = False
colorChanging = False
changeStart = 0
chageTime = 1

fading = False
fadeStart = 0
fadeTime = 1

tutorialDisplayWords = ["click","attention"]
tutorialSpeakWords   = ["click","the","word","when","you","hear","it","we","value","your","attention"]
#tutorialSpeakWords   = ["click","attention"]
realWordPool         = ["because", "results", "track", "you", "health", "instantly", "association", "discover", "love", "guarantee", "proven", "announce", "sponsored", "safety", "hurry", "select", "upgrade", "convince", "study", "find", "subliminal", "watch", "new", "effective", "save", "best", "now", "trial", "story", "free", "increase", "attention", "sex", "number one", "recommended", "try", "money", "persuade", "opportunity", "subscription", "yes", "easy", "compare", "claim", "unique", "personalized", "improvement", "disruptive", "quick", "bargain", "challenge", "influence"]
tutorialMode         = True
lastSpokenWord       = ""
lastSpokenIndex      = -1
lastSpeakTime        = clock()
timeBetweenWords     = 1

displayWord = tutorialDisplayWords[0]
wordPool = tutorialSpeakWords

timeout = 600
lastInput = clock()
displayWordChance = 0.05

#flash red for 0.5 seconds
errorTime = 0.5
erroring =  False
lastError = 0

pwm = None

def reset():
    global bgColor, fgColor, colorChanged, colorChanging, tutorialMode
    global displayWord, wordPool, lastSpokenWord, lastSpokenIndex
    global displayWordChance
    bgColor = white
    fgColor = black
    colorChanged = False
    colorChanging = False

    tutorialMode = True
    wordPool = tutorialSpeakWords
    displayWord = tutorialDisplayWords[0]
    lastSpokenWord = ""
    lastSpokenIndex = -1

    displayWordChance = .05
    

def initwords():
    for word in tutorialSpeakWords+realWordPool:
        if not os.path.isfile(os.path.join("words",word)):
            tts = gTTS(text=word,lang='en')
            tts.save(os.path.join("words",word))

def speakWord(word):
    global lastSpeakTime,lastSpokenWord,lastSpokenIndex
    lastSpeakTime = clock()
    lastSpokenWord = word
    lastSpokenIndex = wordPool.index(word)

    subprocess.Popen(["mpg123",os.path.join("words",word)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def onClick():
    global displayWord, fading, fadeStart, colorChanging, changeStart, wordPool
    global tutorialMode, lastSpeakTime, fgColor, lastError, erroring
    global displayWordChance
    if tutorialMode:
        if lastSpokenWord == displayWord:
            #success
            wordIndex = tutorialDisplayWords.index(displayWord)
            nextWordIndex = wordIndex + 1
            if nextWordIndex < len(tutorialDisplayWords):
                displayWord = tutorialDisplayWords[nextWordIndex]
                fading = True
                fadeStart = clock()
            else:
                tutorialMode = False
                colorChanging = True
                fading = True
                fadeStart = clock()
                changeStart = clock()
                wordPool = realWordPool
                displayWord = random.choice(wordPool)
                dispense()
        else:
            #penalize failure
            lastSpeakTime = clock()
            lastError = clock()
            erroring = True
            fgColor = red
    else:
        #not tutorial mode
        if lastSpokenWord == displayWord:
            #success
            fading = True
            fadeStart = clock()
            displayWord = random.choice(wordPool)
            displayWordChance *= .5
            dispense()
        else:
            #penalize failure
            lastSpeakTime = clock()
            lastError = clock()
            erroring = True
            fgColor = red



def displayText(screen, msg):
    text = pygame.font.Font('freesansbold.ttf',115)
    textSurface = text.render(msg, True, fgColor)
    textRect = textSurface.get_rect()

    surface = pygame.Surface(textRect.size)
    surface.fill(bgColor)
    surface.blit(textSurface, textRect)
    global fading
    if fading:
        u = (clock()-fadeStart)/fadeTime
        if u<1:
            surface.set_alpha(255*u)
        else:
            fading = False

    textRect.center = (WIDTH/2,HEIGHT/2)
    screen.blit(surface, textRect)
    return textRect

def displayCursor(screen, image, pos):
    screen.blit(image,pos)

def main():
    initwords()
    pygame.init()
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(3, GPIO.OUT)
    global pwm
    pwm = GPIO.PWM(3, 50)
    pwm.start(0)

    pygame.display.set_caption("May I Have Your Attention Please")
    screen = pygame.display.set_mode((WIDTH,HEIGHT), pygame.DOUBLEBUF)
    pygame.display.toggle_fullscreen()
    running = True
    textRect = None

    pointerImage = pygame.image.load("hand.png")
    defaultImage = pygame.image.load("point.png");
    pointerHotspot = (5,0)

    pygame.mouse.set_visible(False)#this is to fix stuttering on raspi

    global colorChanging, colorChanged, changeStart, bgColor, fgColor
    global fading, fadeStart
    global lastInput

    while running:
        onBox = textRect is not None and textRect.collidepoint(pos)
        pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                lastInput = clock()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                lastInput = clock()
                if onBox:
                    onClick()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pygame.display.toggle_fullscreen()

        if colorChanging:
            u = (clock()-changeStart)/chageTime
            if u<1:
                bgColor = black*u+white*(1-u)
                fgColor = white*u+black*(1-u)
            else:
                bgColor = black
                fgColor = white
                colorChanging = False
                colorChanged =  True

        if clock()-lastSpeakTime > timeBetweenWords:
            if tutorialMode:
                wordIndex = (lastSpokenIndex+1) % len(wordPool) #wrap to beginning
                word = wordPool[wordIndex]
                speakWord(word)
            else:
                if random.uniform(0,1)<displayWordChance:
                    word = displayWord
                else:
                    word = random.choice(wordPool)
                    while word == displayWord:
                        word = random.choice(wordPool)
                
                speakWord(word)

        if erroring and clock()-lastError > errorTime:
            fgColor = black if tutorialMode else white

        if not tutorialMode and clock()-lastInput > timeout:
            reset()

        screen.fill(bgColor)
        textRect = displayText(screen, displayWord)

        if onBox:
            displayPos = np.subtract(pos,pointerHotspot)
            displayCursor(screen, pointerImage, displayPos)
        else:
            displayCursor(screen, defaultImage, pos)
        pygame.display.update()
        
    pwm.stop()
    GPIO.cleanup()
    pygame.quit()


def setAngle(angle):
    duty = angle/18+2
    GPIO.output(3, True)
    pwm.ChangeDutyCycle(duty)

def dispense():
    GPIO.output(3, True)
    setAngle(115)
    time.sleep(.35)
    setAngle(40)
    time.sleep(.35)
    GPIO.output(3, False)
    pwm.ChangeDutyCycle(0)

if __name__ == "__main__":
    main()
        

    
