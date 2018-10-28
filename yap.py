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

WIDTH = 1440
HEIGHT = 900

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
tutorialSpeakWords   = ["click","attention"]
realWordPool         = ["this","is","a","test"]
tutorialMode         = True
lastSpokenWord       = ""
lastSpokenIndex      = -1
lastSpeakTime        = time.clock()
timeBetweenWords     = 2

displayWord = tutorialDisplayWords[0]
wordPool = tutorialSpeakWords

timeout = 60
lastInput = time.clock()
displayWordChance = 0.1

#flash red for 0.5 seconds
errorTime = 0.5
erroring =  False
lastError = 0

def reset():
    global bgColor, fgColor, colorChanged, colorChanging, tutorialMode
    global displayWord, wordPool, lastSpokenWord, lastSpokenIndex
    bgColor = white
    fgColor = black
    colorChanged = False
    colorChanging = False

    tutorialMode = True
    wordPool = tutorialSpeakWords
    displayWord = tutorialDisplayWords[0]
    lastSpokenWord = ""
    lastSpokenIndex = -1

def initwords():
    for word in tutorialSpeakWords+realWordPool:
        if not os.path.isfile(os.path.join("words",word)):
            tts = gTTS(text=word,lang='en')
            tts.save(os.path.join("words",word))

def speakWord(word):
    global lastSpeakTime,lastSpokenWord,lastSpokenIndex
    lastSpeakTime = time.clock()
    lastSpokenWord = word
    lastSpokenIndex = wordPool.index(word)

    subprocess.Popen(["mpg123",os.path.join("words",word)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def onClick():
    global displayWord, fading, fadeStart, colorChanging, changeStart, wordPool
    global tutorialMode, lastSpeakTime, fgColor, lastError, erroring
    if tutorialMode:
        if lastSpokenWord == displayWord:
            #success
            wordIndex = tutorialDisplayWords.index(displayWord)
            nextWordIndex = wordIndex + 1
            if nextWordIndex < len(tutorialDisplayWords):
                displayWord = tutorialDisplayWords[nextWordIndex]
                fading = True
                fadeStart = time.clock()
            else:
                tutorialMode = False
                colorChanging = True
                fading = True
                fadeStart = time.clock()
                changeStart = time.clock()
                lastSpeakTime = time.clock()+chageTime
                wordPool = realWordPool
                displayWord = random.choice(wordPool)
        else:
            #penalize failure
            lastSpeakTime = time.clock()+timeBetweenWords
            lastError = time.clock()
            erroring = True
            fgColor = red
    else:
        #not tutorial mode
        if lastSpokenWord == displayWord:
            #success
            fading = True
            fadeStart = time.clock()
            displayWord = random.choice(wordPool)
        else:
            #penalize failure
            lastSpeakTime = time.clock()+timeBetweenWords
            lastError = time.clock()
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
        u = (time.clock()-fadeStart)/fadeTime
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


    pygame.display.set_caption("May I Have Your Attention Please")
    screen = pygame.display.set_mode((WIDTH,HEIGHT))
    running = True
    textRect = None

    pointerImage = pygame.image.load("hand.png")
    pointerHotspot = (6,2)

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
                lastInput = time.clock()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                lastInput = time.clock()
                if onBox:
                    onClick()

        if colorChanging:
            u = (time.clock()-changeStart)/chageTime
            if u<1:
                bgColor = black*u+white*(1-u)
                fgColor = white*u+black*(1-u)
            else:
                bgColor = black
                fgColor = white
                colorChanging = False
                colorChanged =  True

        if time.clock()-lastSpeakTime > timeBetweenWords:
            if tutorialMode:
                wordIndex = (lastSpokenIndex+1) % len(wordPool) #wrap to beginning
                word = wordPool[wordIndex]
                speakWord(word)
            else:
                word = random.choice(wordPool)
                if random.uniform(0,1)<displayWordChance:
                    word = displayWord
                speakWord(word)

        if erroring and time.clock()-lastError > errorTime:
            fgColor = black if tutorialMode else white

        if not tutorialMode and time.clock()-lastInput > timeout:
            reset()

        screen.fill(bgColor)
        textRect = displayText(screen, displayWord)

        if onBox:
            displayPos = np.subtract(pos,pointerHotspot)
            displayCursor(screen, pointerImage, displayPos)
            pygame.mouse.set_visible(False)
        else:
            pygame.mouse.set_visible(True)
        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()
