#! /usr/bin/env python
#
# MOTION HARP (c) 2014, Hector Socas-Navarro (hsocas.iac@gmail.com)
#
# REQUIREMENTS:
#    1) pygame (http://www.pygame.org)
#    2) The Leap Motion SDK (files Leap.py, LeapPython.so, libLeap.so
#         in the run directory)
#
# Recommended: Optionally, run simultaneously the Leap Motion Visualizer 
#  application to see how your hands are being tracked in real time.
# 
#
# COMMENTS AND NOTES:
#
# For better coverage of the lower notes, orient the Leap Motion device
#  with the USB connnector pointing left. This will give it a better view
#  of your left hand near the leftmost edge of the detection box.
#  
# Using commands module instead of subprocess to spawn OS commands because,
# even though the later is the preferred method, it appears to have better
# performance. Reference: http://stackoverflow.com/questions/10888846/python-subprocess-module-much-slower-than-commands-deprecated
#
# Use examples of under Linux with no external MIDI instrument:
#  To play stand-alone (no play-along mode): 
#     Start qsynth (this will route sound through jack)
#     Run harp.py as normal (select Synth input port at startup)
#     Kill jackd to go back to "normal" pulseaudio sound (killall jackd)
#
#  For play-along mode:
#     If using an external keyboard, it works normally
#     The problem comes if you try to use qsynth because the external song
#     will play through pulseaudio and the motion harp midi notes will
#     play through qsynth using jack. To make them both work simultaneously
#     you could route pulseaudio through jack. To do this:
#       -Start qsynth as usual
#       -Run the following commands:
#          pactl load-module module-jack-sink ; pactl load-module module-jack-source
#       -Start pavucontrol. You'll see jack sink as a new output device
#       -Start motion harp, go to pavucontrol->playback->python and select Jack sink

#
# Instructions
#
#   A note is played when a finger moves relative to the palm of a hand
#   in the direction normal to the palm. In the usual play position with
#   the hands facing down, this means when a finger moves down with
#   respect to the hand. It is important to emphasize that it's the relative
#   motion that matters here. If you move your hand completely rigid up and
#   down, no sound will be played. Some additional considerations are:
#       1) In order to play a note, the finger must be extended and the
#       hand belongs to must be reliably detected by the Leap Motion.
#       2) Once a finger plays a note, it gets locked (meaning it cannot
#       trigger any other notes) until some amount of time has elapsed
#       (0.3 seconds) or until it moves in the opposite direction. However,
#       there are exceptions to this rule and the locks may be released
#       prematurely under certain circumstances described below.
#
#   When a note is played, the pitch is decided first by the finger tip
#   position in the x-direction (left-right). If that position corresponds
#   to a note that is consistent with the current chord selected, then it
#   is played with a volume (MIDI velocity) determined by the position of the
#   finger tip in the z-direction. For z>0 (i.e., from the Leap Motion vertical
#   towards the user), maximum volume is used. For z<0 (from the Leap Motion
#   vertical away from the user), the volume decreases gradually. If the
#   hand is above 22cm from the Leap Motion, then an octave is added,
#   resulting in higher pitch.
#
#   If the note selected by the finger position is not consistent with the
#   current chord, it will be corrected. The closest matching note will be
#   played instead. We can use the parameters strictharmony_left and _right
#   to supress this behavior or to establish a probablity that a given
#   dissonant note will be corrected or played as is. When an uncorrected
#   note is played, the corresponding printout line is preceded with
#   an asterisk sign (*).
#
#   Playing with the hands facing sideways reduces the finger lock time
#   to 0.05 seconds, allowing for fast bursts of a large number of notes.
#   The same effect may be achieved by a fast swipe of the hand in the
#   left-right direction, but in this case the effect lasts for 3 seconds.
#
#   Waving a hand with the palm facing up will introduce Instrument 2
#   (strings) in the melody. Once introduced, the strings will simply
#   follow the changes in chord.
#
#   The sequence of chords to be played must be specified in advance.
#   This is normally done in the song module. A default NoSong.py module
#   contains the parameters to be used when not in play-along mode.
#   For a specific song in the play-along mode, the parameters are
#   given in that song module (e.g., ShowMustGoOn.py). 
#
#   To move forward or backward in the chord progression we can make
#   a pinch or grab gesture with either hand. This will not work in
#   play along mode or, in general, when the variable bartimes is defined
#   in the song module. If bartimes exists, then the chords are updated
#   according to the times specified there.
#
# Basic configuration parameters:
#
# Note: strictharmony might be overriden by song data file
strictharmony_left=1 # How strictly enforce harmony for left hand (0-1)
strictharmony_right=0.9 # How strictly enforce harmony for right hand (0-1)

# For play-along mode, provide song data file (with no extension!)
songdatafile="" # NoSong
#songdatafile="GetLucky" # Leave it blank "" for no play-along mode
#songdatafile="ShowMustGoOn" # Leave it blank "" for no play-along mode
#songdatafile="BohemianRhapsody"
#songdatafile="Imagine"

# Chord sequence to use
#chords2play=['G ','F ','A min','D min','C '] # Canonical
chords2play=['C ','A min','C#','D min','G 7sus4','C 7sus4']

# Change chord by time? If so, set it to time in seconds. If 0, change
#  chords by gestures only
chordstime=0
#
# End of configuration parameters:
#

import Leap, pygame, pygame.midi, sys, os
import commands, chords
from random import choice, random
from time import sleep
import datetime

# Global variables
prevtime=0L
timenow=0L
debug=0
busy=0
fingerlock=[0L]*10
fingnote=[[' ',0]]*10
stringnotes=list()
nframes=10 
releaselocks=0L
pinching=0L
songstart=datetime.datetime.now()
lastchordchange=0L
# For midi
pygame.init()
pygame.midi.init()
midi=pygame.midi.Output(0)
indchord=-1
Instrument1=0 # Grand Piano
Instrument2=49 # Strings
noteson=list()
notesonchan=list()

frames=list()
prevframes=list()

harpvolume=1.0 # Volume normalization factor
if songdatafile == "": # No play-along mode
    songdata=__import__("NoSong")
else: # Import song data from file for play-along mode
    songdata=__import__(songdatafile)

if hasattr(songdata,"bartimes"):
    bartimes=songdata.bartimes # Times at which to change chords

# Note: timedelay is the amount of time in seconds that the song playback
# will be delayed after the chord timing starts

songdata.tuneshift=int(songdata.tuneshift) # Shift up or down the harp notes
strictharmony_left=songdata.strictharmony_left
strictharmony_right=songdata.strictharmony_right
chords2play=songdata.chords2play
if hasattr(songdata,'harpvolume'):
    harpvolume=songdata.harpvolume

class Listnr(Leap.Listener):

    def on_init(self, controller):
        global midi
        import re


# Create frame buffer
        print 'Initializing Leap Motion...'
        itry=0
        while (not controller.frame(2*nframes).is_valid):
            itry+=1
            if itry == 1e6:
                print "Something's not right. Make sure the Leap Motion is connected"
                print 'and the leapd daemon is running'
                pygame.midi.quit()
                os._exit(1)
        for iframe in range(nframes):
            frames.append(controller.frame(iframe))
        print "Frame buffer size:",len(frames)
        print "Initialized"

# Initialize midi
        print "If your keyboard doesn't play, try to find the device input and output"
        print "In Linux you can try:"
        print 'aconnect -i'
        print 'aconnect -o'
        print 'And then:'
        print 'aconnect output_device input_device'
# Example: aconnect -i
# client 14: 'Midi Through' [type=kernel]
# aconnect -o
# client 24: 'PSR-3000' [type=kernel]
# aconnect 24 14

        port=-1
        options=list()
        for tryport in range(40):
            try:
                name=pygame.midi.get_device_info(tryport)[1]
                if name != '':
                    print 'Port ',tryport,':',name
                    options.append(tryport)
            except:
                donothing=1
        while port < 0:
            print 'Choose one of the above. Options are:',options
            try:
                port=int(raw_input())
            except:
                print 'Answer a number from this list:',options

        if port == -1:
            print 'Error finding MIDI port'
            pygame.midi.quit()
            os._exit(1)
        del midi

        try:
            midi=pygame.midi.Output(port)
        except:
            print "Couldn't connect to port, trying the default"
            midi=pygame.midi.Output(0)

# Pygame mixer for external music
        if songdata.songfile != '':
            print 'Playing song from file:',songdata.songfile
            pygame.init()
            pygame.mixer.init()
            pygame.mixer.music.set_volume(songdata.songvolume)
            pygame.mixer.music.load(songdata.songfile)
            pygame.mixer.music.play()
            songstart=datetime.datetime.now()

    def on_connect(self, controller):
        print "Connected"

    def on_disconnect(self, controller):
        # Note: not dispatched when running in a debugger.
        print "Disconnected"

    def on_exit(self, controller):
        pygame.midi.quit()
        print "Exited"

    def on_frame(self, controller):
        global prevtime, releaselocks, indchord, lastchordchange, stringnotes,\
            pinching, songstart

        frame=controller.frame()

        timenow=frame.timestamp
        if ( (timenow - prevtime)*1E-6 < 0.005):
            return
        prevtime=timenow

        midi.set_instrument(Instrument1,0)
        midi.set_instrument(Instrument2,1)

        frames.pop(0) # Remove first element and shift list
        frames.append(frame)
        basenotes=['C ','D ','E ','F ','G ','A ','B ']

# Process each hand 
        for ihand in [0,1]:
            hand=frame.hands[ihand]
            if (hand.confidence > 0.6): 
                palmpos=hand.palm_position
                for finger in hand.fingers: 
                    if finger.is_extended: 
                        fingx=finger.tip_position[0]
                        fingy=finger.tip_position[1]
                        fingz=finger.tip_position[2]
                        fingvx=finger.tip_velocity[0]
                        fingvy=finger.tip_velocity[1]
                        fingvz=finger.tip_velocity[2]
                        velx=hand.palm_velocity[0]
                        vel=hand.palm_velocity[2]
                        roll=hand.palm_normal.roll*Leap.RAD_TO_DEG
                        nfinger=finger.type()
                        if ihand == 1: nfinger=nfinger+5
                        if fingerlock[nfinger] > 0: #locked?
                            timetorelease=0.3 # Adjust
                            if releaselocks != 0:
                                timetorelease=0.05 # Adjust
                            if abs(roll) > 50 and abs(roll) < 120:
                                timetorelease=0.1 # Adjust
                            if (frame.timestamp-fingerlock[nfinger]*1.0)*1E-6 > timetorelease: # Release if locked over some time
                                fingerlock[nfinger]=0.
                                fingnote[nfinger]=[' ',0]
                        
                        if abs(velx) > 500 or releaselocks != 0:
            # release all locks if moving horizontally or upwards
                            if releaselocks == 0: 
                                releaselocks = frame.timestamp
                                print '**Releasing locks for 3 seconds',velx
                            else:
                                if (frame.timestamp - releaselocks)*1e-6 > 3:
                                    releaselocks = 0
                                    print '**Locks back in place'

                        projectedvel=(finger.tip_velocity-hand.palm_velocity).dot(hand.palm_normal) # Relative tip velocity projected down from palm normal
                        projectedtip=(finger.tip_position-hand.stabilized_palm_position)
                        projectedtip=projectedtip.normalized
                        projectedtip=projectedtip.dot(hand.palm_normal)

                        if projectedvel < 0: # Release finger if moving up
                            fingerlock[nfinger]=0.
                            fingnote[nfinger]=[' ',0]
                        if projectedvel > 150 : # Play note. Adjust sensitivity
                            if fingerlock[nfinger] == 0:
                                volume=abs(250-min(abs(fingz),250))/250.
                                volume=int(volume*120.)
                                volume=max(volume,10)
                                volume=min(volume,120)
                                volume=int(volume*harpvolume)
                                px=(fingx+200)
                                px=min(px,400.)
                                px=max(px,0.)
                                py=hand.stabilized_palm_position[1]

                                # Free-style play
                                char='*'
                                px=(fingx+200)
                                px=min(px,400.)
                                px=max(px,0.)
                                octave_shft=int(px/100.)-3
                                if py > 230: 
                                    octave_shft=octave_shft+1
                                idx=px % 100
                                idx=int(idx/100.*7)
                                note=basenotes[idx]
                                strictharmony=strictharmony_left
                                if hand.is_right:
                                    strictharmony=strictharmony_right
                                if random() < strictharmony: # Harmonic note
                                    char=''
                                    notes=chords.ChordKeys[chords2play[indchord]]
                                    noteidx=basenotes.index(note)
                                    mindif=1e6
                                    closest=''
                                    for n in notes:
                                        n2=n[0][0]+' '
                                        i=basenotes.index(n2)
                                        dif=abs(i-noteidx)
                                        if dif < mindif:
                                            mindif=dif
                                            closest=n
                                        dif=abs((i+7)-noteidx)
                                        if dif < mindif:
                                            mindif=dif
                                            closest=n
                                        dif=abs((i-7)-noteidx)
                                        if dif < mindif:
                                            mindif=dif
                                            closest=n
                                    note=closest
                                    if nfinger > 0:
                                        prevnote=fingnote[nfinger-1][0]
                                        prevoct=fingnote[nfinger-1][1]
                                        if prevnote != ' ':
                                            octave_shft=prevoct
                                            if not prevnote in notes:
                                                prevnote=notes[0]
                                            else:
                                                idx=notes.index(prevnote)
                                                if idx == len(notes)-1:
                                                    idx=0
                                                    octave_shft=octave_shft+1
                                                else:
                                                    note=notes[idx+1]
                                    elif nfinger < 9:
                                        prevnote=fingnote[nfinger+1][0]
                                        prevoct=fingnote[nfinger+1][1]
                                        if prevnote != ' ':
                                            octave_shft=prevoct
                                            if not prevnote in notes:
                                                prevnote=notes[len(notes)-1]
                                            else:
                                                idx=notes.index(prevnote)
                                                if idx == 0:
                                                    idx=len(notes)-1
                                                    octave_shft=octave_shft+1
                                                else:
                                                    note=notes[idx-1]

                                octave_shft=max(octave_shft,-4)
                                octave_shft=min(octave_shft,4)
                                notenum=72+chords.semitones[note]+octave_shft*12
                                notenum=max(notenum,0)
                                notenum=min(notenum,127)
                                midi.note_off(notenum+songdata.tuneshift,0,0)
                                midi.note_on(notenum+songdata.tuneshift,volume,0)
                                noteson.append(notenum)
                                notesonchan.append(0)
                                fingerlock[nfinger] = frame.timestamp
                                fingnote[nfinger]=[note,octave_shft]
                                print char+'Chord:'+chords2play[indchord]+' Finger:'+str(nfinger)+', Note:'+note+', volume:',volume,' octave:',octave_shft

                        changechordnow=0
                        if not 'bartimes' in globals(): # No play-along mode
                            if hand.pinch_strength > 0.7 or hand.grab_strength > 0.7: # Gesture to change
                                if pinching == 0:
                                    pinching=frame.timestamp
                                    changechordnow=1
                                if ( (frame.timestamp-pinching)*1e-6 > 0.5):
                                    pinching=0L
                            if chordstime > 0: # Change after some time
                                if (frame.timestamp-lastchordchange)*1e-6 > chordstime:
                                    changechordnow=1
                                    lastchordchange=frame.timestamp

                        if changechordnow == 1: # Change chord
                            if ihand == 0:
                                indchord=indchord-1
                            else:
                                indchord=indchord+1
                            if indchord < 0:
                                indchord=len(chords2play)-1
                            if indchord > len(chords2play)-1:
                                indchord=0
                            print ' Chord switch to ',chords2play[indchord]
                        addstringnote=0
                        changestringnote=0
                        if len(stringnotes) == 0: 
                            if abs(roll) > 160: # Strings
                                addstringnote=1
                        else:
                            if not stringnotes[0] in chords2play[indchord]:
                                changestringnote=1
                        if addstringnote == 1 or changestringnote:
                            volume=127-int((palmpos[1]-50)/350.*125)
                            volume=int(volume/2.)
                            volume=max(volume,10)
                            volume=min(volume,127)
                            volume=int(volume*harpvolume)
                            octave_shft=int(palmpos[0]/200.*4.)
                            octave_shft=octave_shft-1
                            octave_shft=max(octave_shft,-2)
                            octave_shft=min(octave_shft,2)
                            for note in stringnotes[1:]:
                                midi.note_off(note+songdata.tuneshift,0,1)
                            stringnotes=list()
                            stringnotes.append(chords2play[indchord])
                            note=chords.ChordKeys[chords2play[indchord]][0]
                            notevalue=72+chords.semitones[note]+octave_shft*12
                            stringnotes.append(notevalue)
                            midi.note_on(notevalue+songdata.tuneshift,volume,1)
                            noteson.append(notevalue)
                            notesonchan.append(1)

                            print 'Chord:',chords2play[indchord],' string note=',note,volume

                        while len(noteson) > 20:
                            removenote=noteson[0]
                            removechan=notesonchan[0]
                            noteson.pop(0)
                            notesonchan.pop(0)
                            if not removenote in noteson:
                                midi.note_off(removenote+songdata.tuneshift,0,removechan)
            # If play-along mode, check if update chords
            if 'bartimes' in globals():
#                if (songstart == 0):
#                    songstart=frame.timestamp
#                else:
                if 1 == 1:
                    songtime=datetime.datetime.now()-(songstart+datetime.timedelta(0,songdata.timedelay))
                    songtime=songtime.total_seconds()
                    # if abs(songtime*10-int(songtime*10))<1.:
                    #    print 'st=',songtime,(datetime.datetime.now()-songstart).total_seconds()
                    while songtime > bartimes[len(bartimes)-1]+10: # Cycle if past end of song
                        songtime=songtime-bartimes[len(bartimes)-1]

                    for i0 in range(len(bartimes)-1):
                        if songtime < bartimes[0]:
                            if i0 != indchord:
                                print 'Starting with chord 1:',chords2play[0]
                                indchord = 0
                            break
                        if songtime >= bartimes[i0] and songtime < bartimes[i0+1]:
                            if i0 != indchord:
                                indchord=i0
                                print ' Chord switch to ',indchord+1,':',chords2play[indchord]#,' time:',songtime,bartimes[i0],bartimes[i0+1]
                            break



    def state_string(self, state):
        if state == Leap.Gesture.STATE_START:
            return "STATE_START"

        if state == Leap.Gesture.STATE_UPDATE:
            return "STATE_UPDATE"

        if state == Leap.Gesture.STATE_STOP:
            return "STATE_STOP"

        if state == Leap.Gesture.STATE_INVALID:
            return "STATE_INVALID"

def main():
    # Create a sample listener and controller
    listener = Listnr()
    controller = Leap.Controller()

    # Have the sample listener receive events from the controller
    controller.add_listener(listener)

    # Keep this process running until Enter is pressed
    print "Press Enter to quit..."
    sys.stdin.readline()
    for idx in range(128):
        midi.note_off(idx,0,0)
    for idx in range(128):
        midi.note_off(idx,0,1)
    os._exit(1)

    # Remove the sample listener when done
    pygame.midi.quit()
    controller.remove_listener(listener)
    

if __name__ == "__main__":
    main()
