#! /usr/bin/env python
# 
# (2013) Hector Socas Navarro (hsocas.iac@gmail.com): MOTION HARP
#
# Requirements:
#   * Python
#   * pygame
#   * python-Xlib (only to get screen resolution)
#   * LeapMotion SDK
#   * if not in your path, LeapSDK/lib/Leap.py and LeapSDK/lib/x??/LeapPython.so
#        must be present in the running directory
#
# Instructions:
#
#   * Notes are triggered when a finger moves down and released when it moves up.
#   * A finger is locked and may not trigger another note until one of the
#      following conditions are met:
#       a)It moves up again
#       b)0.5 seconds from the last note have passed
#       c)All locks are released (see below)
#   * If a hand moves fast in the horizontal direction, all locks are
#      released and remain that way for the next 2 seconds, allowing 
#      for quick note bursts.
#   * The notes triggered are picked randomly from the current chord, 
#      except for the free-style mode described below. The octave is
#   *  determined by the position of the finger in the left-right direction
#   * The current chord is changed by moving hands forward or backward
#   * The height of the hand that plays a note determines its volume
#   * If the hand is higher than 250 mm, then notes are not bound to 
#      current chord any more allowing for a more free-style playing.
#      However, not every note is permitted even in this mode to avoid
#      dissonances. Only notes from the current key are played
#   * Showing a hand with the palm facing up brings up the strings.
#      When strings are on they always play the first note in the
#      current chord. The hand may still be moved to change
#      chord and therefore the string note without playing piano notes.
#      However, even with the palm facing up, vertical finger movement
#      will trigger piano notes
#
#  NOTE: This program does not render sound. You need a MIDI instrument
#  or software synthesizer to hear the music. Under Linux you can
#  use e.g. qsynth as a synthesizer. Once started you should see it in
#  the list of available ports shown when you start Motion Harp. 
#  If you're using qsynth it will appear as "Synth input port" in the 
#  port list. 
#
# Using commands module instead of subprocess to spawn OS commands because,
# even though the later is the preferred method, it appears to have better
# performance. Reference: http://stackoverflow.com/questions/10888846/python-subprocess-module-much-slower-than-commands-deprecated

import Leap, pygame, pygame.midi, sys, os
from time import sleep, clock
from Xlib import X, display

class Listnr(Leap.Listener):
    debug=0
    busy=0
    screenx=0
    screeny=0
    scalex=1.0
    scaley=1.0
    offsety=20.
    offsetx=-100.
    maxnfingers=30
    fingerlock=[0L]*maxnfingers
    stringnotes=list()
    nframes=10 # frames to average
    releaselocks=0L
# For X
    gc=0
    root=0
# For midi
    pygame.init()
    pygame.midi.init()
    midi=pygame.midi.Output(0)
    indchord=0
    Instrument1=0 # Grand Piano
    Instrument2=49 # Strings
    noteson=list()
    notesonchan=list()

    frames=list()
    prevframes=list()

    def on_init(self, controller):
        import subprocess, re
        from time import sleep
# Get screen resolution
        displ=display.Display()
        s=displ.screen()
        Listnr.root=s.root
        Listnr.screenx=s.width_in_pixels
        Listnr.screeny=s.height_in_pixels
        print "Screen size is:",Listnr.screenx,Listnr.screeny
# Initialize midi
#        subprocess.call(['aconnect',midiclientout,midiclientin])
        print "If your keyboard doesn't play, try to find the device input and output"
        print 'aconnect -i'
        print 'aconnect -o'
        print 'And then:'
        print 'aconnect output_device input_device'

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
        del Listnr.midi

        try:
            Listnr.midi=pygame.midi.Output(port)
        except:
            print "Couldn't connect to port, trying the default"
            Listnr.midi=pygame.midi.Output(0)

# Open file with debug output
        if Listnr.debug == 1:
            f=open('output.txt','w')
            for ind in range(5): f.write(str(ind)+'\n')
            f.close()
# Create frame buffer
        print 'Initializing Leap Motion...'
        time0=clock()
        while (not controller.frame(2*Listnr.nframes).is_valid):
            if clock()-time0 > 5:
                print "Timeout waiting for valid frames from the Leap Motion."
                print "Something's not right. Make sure the Leap Motion is connected"
                print 'and the leapd daemon is running'
                sys.exit(1)
        for iframe in range(Listnr.nframes):
            Listnr.frames.append(controller.frame(iframe))
            Listnr.prevframes.append(controller.frame(iframe+Listnr.nframes))
        print "Frame buffer sizes:",len(Listnr.frames),len(Listnr.prevframes)
        print "Initialized"

    def on_connect(self, controller):
        print "Connected"

        # Enable gestures

# debug, circles disabled
#        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);

    def on_disconnect(self, controller):
        # Note: not dispatched when running in a debugger.
        print "Disconnected"

    def on_exit(self, controller):
        pygame.midi.quit()
        print "Exited"

    def on_frame(self, controller):

        def flush_buffer():
            Listnr.prevframes[0:Listnr.nframes]=Listnr.frames[0:Listnr.nframes]

        import chords
        from subprocess import call
        from time import sleep
        from random import choice
        try:
            import commands
        except:
            donothing=1

        debug = Listnr.debug
        mnfing = Listnr.maxnfingers
        chords2play=['G ','F ','A min','D min','C ']

        currentframe=controller.frame()

        nframes2=int(Listnr.nframes/2) # Use few frames for pointing to avoid lag
        nframes=Listnr.nframes

        Listnr.midi.set_instrument(Listnr.Instrument1,0)
        Listnr.midi.set_instrument(Listnr.Instrument2,1)

        Listnr.prevframes.pop(0) # Remove first element and shift list
        Listnr.prevframes.append(Listnr.frames[0])
        Listnr.frames.pop(0) # Remove first element and shift list
        Listnr.frames.append(currentframe)

        basenotes=['C ','D ','E ','F ','G ','A ','B ']

        numfingers=len(currentframe.hands[0].fingers)
# Get average quantities from frame collections
        norm=1./Listnr.nframes
        norm2=1./(nframes-nframes2+1)
        prevavfingx=[0.]*mnfing
        prevavfingy=[0.]*mnfing
        prevavfingz=[0.]*mnfing
        avfingx=[0.]*mnfing
        avfingy=[0.]*mnfing
        avfingz=[0.]*mnfing
        avfingvx=[0.]*mnfing
        avfingvy=[0.]*mnfing
        avfingvz=[0.]*mnfing
        fingnote=[0]*mnfing
        avfinghand=[0]*mnfing
        validfinger=[0]*mnfing
        avtime=sum(Fr.timestamp for Fr in Listnr.frames)*norm
        prevavtime=sum(Fr.timestamp for Fr in Listnr.prevframes)*norm
        avnhands=sum(len(Fr.hands) for Fr in Listnr.frames)*norm
        prevavnhands=sum(len(Fr.hands) for Fr in Listnr.prevframes)*norm
        avpitch=sum(Fr.hands[0].direction.pitch for Fr in Listnr.frames)*Leap.RAD_TO_DEG*norm
        avroll=sum(Fr.hands[0].palm_normal.roll for Fr in Listnr.frames)*Leap.RAD_TO_DEG*norm
        avsphere=sum(Fr.hands[0].sphere_radius for Fr in Listnr.frames)*norm
        prevavpitch=sum(Fr.hands[0].direction.pitch for Fr in Listnr.prevframes)*Leap.RAD_TO_DEG*norm
        prevavroll=sum(Fr.hands[0].palm_normal.roll for Fr in Listnr.prevframes)*Leap.RAD_TO_DEG*norm
        avnumfingers=sum(len(Fr.hands[0].fingers) for Fr in Listnr.frames)*norm
        prevavnumfingers=sum(len(Fr.hands[0].fingers) for Fr in Listnr.prevframes)*norm

        avpos1=[0.,0.,0.]
        avvel1=[0.,0.,0.]
        avroll1=0.
        avroll2=0.
        nadded=0
        naddedfing=[0]*mnfing
        for Fr in Listnr.frames[0:nframes]:
            if Fr.hands[0].is_valid:
                avpos1[0]+=Fr.hands[0].palm_position[0]
                avpos1[1]+=Fr.hands[0].palm_position[1]
                avpos1[2]+=Fr.hands[0].palm_position[2]
                avvel1[0]+=Fr.hands[0].palm_velocity[0]
                avvel1[1]+=Fr.hands[0].palm_velocity[1]
                avvel1[2]+=Fr.hands[0].palm_velocity[2]
                avroll1+=Fr.hands[0].palm_normal.roll
                nadded+=1
                for finger in Fr.hands[0].fingers:
                    fid=finger.id
                    if fid > len(avfingx):
                        print 'Warning!!, fid=',fid
                        for i in range(20):
                            print ''
                    avfingx[fid]+=finger.tip_position[0]
                    avfingy[fid]+=finger.tip_position[1]
                    avfingz[fid]+=finger.tip_position[2]
                    avfingvx[fid]+=finger.tip_velocity[0]
                    avfingvy[fid]+=finger.tip_velocity[1]
                    avfingvz[fid]+=finger.tip_velocity[2]
                    avfinghand[fid]+=0
                    naddedfing[fid]+=1
        if nadded > 0:
            avpos1[0:3]=[x*1./nadded for x in avpos1]
            avvel1[0:3]=[x*1./nadded for x in avvel1]
            avroll1=avroll1*Leap.RAD_TO_DEG/nadded

        avpos2=[0.,0.,0.]
        avvel2=[0.,0.,0.]
        nadded=0
        for Fr in Listnr.frames[0:nframes]:
            if Fr.hands[1].is_valid:
                avpos2[0]+=Fr.hands[1].palm_position[0]
                avpos2[1]+=Fr.hands[1].palm_position[1]
                avpos2[2]+=Fr.hands[1].palm_position[2]
                avvel2[0]+=Fr.hands[1].palm_velocity[0]
                avvel2[1]+=Fr.hands[1].palm_velocity[1]
                avvel2[2]+=Fr.hands[1].palm_velocity[2]
                avroll2+=Fr.hands[1].palm_normal.roll
                nadded+=1
                for finger in Fr.hands[1].fingers:
                    fid=finger.id
                    if fid > len(avfingx):
                        print 'Warning!!, fid=',fid
                        for i in range(20):
                            print ''
                    avfingx[fid]+=finger.tip_position[0]
                    avfingy[fid]+=finger.tip_position[1]
                    avfingz[fid]+=finger.tip_position[2]
                    avfingvx[fid]+=finger.tip_velocity[0]
                    avfingvy[fid]+=finger.tip_velocity[1]
                    avfingvz[fid]+=finger.tip_velocity[2]
                    avfinghand[fid]+=1
                    naddedfing[fid]+=1
        if nadded > 0:
            avpos2[0:3]=[x*1./nadded for x in avpos2]
            avvel2[0:3]=[x*1./nadded for x in avvel2]
            avroll2=avroll2*Leap.RAD_TO_DEG/nadded
        for idx in range(mnfing):
            if naddedfing[idx] > 0:
                avfingx[idx]=avfingx[idx]*1./naddedfing[idx]
                avfingy[idx]=avfingy[idx]*1./naddedfing[idx]
                avfingz[idx]=avfingz[idx]*1./naddedfing[idx]
                avfingvx[idx]=avfingvx[idx]*1./naddedfing[idx]
                avfingvy[idx]=avfingvy[idx]*1./naddedfing[idx]
                avfingvz[idx]=avfingvz[idx]*1./naddedfing[idx]
                avfinghand[idx]=avfinghand[idx]*1./naddedfing[idx]
                if naddedfing[idx] > 2 and (avfinghand[idx] < 0.1 or avfinghand[idx] > 0.9): # Set this finger as a valid one
                    validfinger[idx]=1

        naddedfing=[0]*mnfing
        for Fr in Listnr.prevframes[0:nframes]:
            if Fr.hands[0].is_valid:
                for finger in Fr.hands[0].fingers:
                    fid=finger.id
                    if fid > len(avfingx):
                        print 'Warning!!, fid=',fid
                        for i in range(20):
                            print ''
                    prevavfingx[fid]+=finger.tip_position[0]
                    prevavfingy[fid]+=finger.tip_position[1]
                    prevavfingz[fid]+=finger.tip_position[2]
                    naddedfing[fid]+=1
        for Fr in Listnr.prevframes[0:nframes]:
            if Fr.hands[1].is_valid:
                for finger in Fr.hands[1].fingers:
                    fid=finger.id
                    if fid > len(avfingx):
                        print 'Warning!!, fid=',fid
                        for i in range(20):
                            print ''
                    prevavfingx[fid]+=finger.tip_position[0]
                    prevavfingy[fid]+=finger.tip_position[1]
                    prevavfingz[fid]+=finger.tip_position[2]
                    naddedfing[fid]+=1
        for idx in range(mnfing):
            if naddedfing[idx] > 0:
                prevavfingx[idx]=prevavfingx[idx]*1./naddedfing[idx]
                prevavfingy[idx]=prevavfingy[idx]*1./naddedfing[idx]
                prevavfingz[idx]=prevavfingz[idx]*1./naddedfing[idx]



        if avnhands > 0.5:
            for hand in currentframe.hands:
                palmpos=[0.,0.,0.]
                for finger in hand.fingers: # Loop in fingers
                    fid=finger.id
                    if Listnr.fingerlock[fid] > 0: #locked?
                        if (currentframe.timestamp-Listnr.fingerlock[fid]*1.0)*1E-6 > 1:          # Release if locked over some time
                            Listnr.fingerlock[fid]=0.
                    if validfinger[fid] == 1:
                        handid=int(avfinghand[fid])
                        pos=[avfingx[fid],avfingy[fid],avfingz[fid]]
                        if handid == 0:
                            palmpos=[avpos1[0],avpos1[1],avpos1[2]]
                            avvel=avvel1
                        else:
                            palmpos=[avpos2[0],avpos2[1],avpos2[2]]
                            avvel=avvel2
    # release all locks if moving horizontally or upwards
                        if abs(avvel[0]) > 1000 or Listnr.releaselocks != 0: 
                            if Listnr.releaselocks == 0: 
                                Listnr.releaselocks = currentframe.timestamp
                                print 'releasing locks for 2 seconds'#,avvel
                            else:
                                if (currentframe.timestamp - Listnr.releaselocks)*1e-6 > 2:
                                    Listnr.releaselocks = 0
                                    print 'locks back in place'
                            for idx in range(mnfing):
                                Listnr.fingerlock[idx]=0.

                        fingnote[finger.id]=0
                        if avfingy[fid]-prevavfingy[fid] < -10 and \
                                abs(avfingy[fid]-prevavfingy[fid]) < 50 and \
                                    Listnr.fingerlock[finger.id] == 0: # Play note
                            coordx=((pos[0]-Listnr.offsetx)+200.)/400.*Listnr.screenx
                            coordx=min(coordx,Listnr.screenx)
                            coordx=max(coordx,0)
                            coordy=(1.-((pos[1]-Listnr.offsety))/400.)*Listnr.screeny
                            coordy=min(coordy,Listnr.screeny)
                            coordy=max(coordy,0)
                            Listnr.root.warp_pointer(coordx,coordy)
                            notes=chords.ChordKeys[chords2play[Listnr.indchord]]
                            if pos[1] < 250:
                                note=choice(notes)
                                volume=127-int((pos[1]-100)/200.*125)
                                octave_shft=int(pos[0]/200.*3.)
                                octave_shft=octave_shft-1
                                notenum=72+chords.semitones[note]+octave_shft*12
                                harmonic=1
                                hchar=''
                            else:
                                notenum=int((pos[0]+250.)/400.*len(basenotes))*3
                                octave_shft=-2
                                if notenum >= 7: octave_shft+=1
                                if notenum >= 14: octave_shft+=1
                                if notenum >= 21: octave_shft+=1
                                note=chords.rotating_idx(basenotes,notenum)
                                chordroot=chords2play[Listnr.indchord]
                                chordroot=chordroot[0:2]
                                notenum=72+chords.semitones[note]+chords.semitones[chordroot]+12*octave_shft
                                volume=127-int((pos[1]-250.)/200.*125)
                                harmonic=0
                                hchar='*'
                            volume=max(volume,10)
                            volume=min(volume,127)
                            ocatve_shft=max(octave_shft,-4)
                            ocatve_shft=min(octave_shft,4)
                            notenum=max(notenum,0)
                            notenum=min(notenum,127)
                            if Listnr.fingerlock[finger.id] == 0:
                                Listnr.midi.note_off(notenum,0,0)
                                Listnr.midi.note_on(notenum,volume,0)
                                Listnr.noteson.append(notenum)
                                Listnr.notesonchan.append(0)
                                Listnr.fingerlock[finger.id] = currentframe.timestamp
                                print hchar+'Chord:'+chords2play[Listnr.indchord]+' Finger:'+str(fid)+', Note:'+note+', volume:',volume,' octave:',octave_shft,' hand=',avfinghand[fid]

                            # Update chord when piano key pressed
                            Listnr.indchord=int(palmpos[2]/200.*len(chords2play))
                            Listnr.indchord=max(Listnr.indchord,0)
                            Listnr.indchord=min(Listnr.indchord,len(chords2play)-1)


                        if avfingy[fid] > prevavfingy[fid]+10 or avfingvy[fid] > 40: # If finger moves up, release locks
                            Listnr.fingerlock[fid] = 0


                    # Update chord when palm up
                    if abs(avroll1) > 160 or abs(avroll2)>160:
                        Listnr.indchord=int(palmpos[2]/200.*len(chords2play))
                        Listnr.indchord=max(Listnr.indchord,0)
                        Listnr.indchord=min(Listnr.indchord,len(chords2play)-1)
                    addstringnote=0
                    changestringnote=0
                    if len(Listnr.stringnotes) == 0: 
                        if abs(avroll1) > 160 or abs(avroll2)>160: # Strings
                            addstringnote=1
                    else:
                        if not Listnr.stringnotes[0] in chords2play[Listnr.indchord]:
                            changestringnote=1
                    if addstringnote == 1 or changestringnote == 1:
                        volume=127-int((palmpos[1]-50)/350.*125)
                        volume=int(volume/2.)
                        volume=max(volume,10)
                        volume=min(volume,127)
                        octave_shft=int(palmpos[0]/200.*4.)
                        octave_shft=octave_shft-1
                        ocatve_shft=max(octave_shft,-2)
                        ocatve_shft=min(octave_shft,2)
                        for note in Listnr.stringnotes[1:]:
                            Listnr.midi.note_off(note,0,1)
                        Listnr.stringnotes=list()
                        Listnr.stringnotes.append(chords2play[Listnr.indchord])
                        note=chords.ChordKeys[chords2play[Listnr.indchord]][0]
                        notevalue=72+chords.semitones[note]+octave_shft*12
                        Listnr.stringnotes.append(notevalue)
                        Listnr.midi.note_on(notevalue,volume,1)
                        Listnr.noteson.append(notevalue)
                        Listnr.notesonchan.append(1)
                        
                        print 'Chord:',chords2play[Listnr.indchord],' string note=',note,volume



                while len(Listnr.noteson) > 15:
                    removenote=Listnr.noteson[0]
                    removechan=Listnr.notesonchan[0]
                    Listnr.noteson.pop(0)
                    Listnr.notesonchan.pop(0)
                    if not removenote in Listnr.noteson:
                        Listnr.midi.note_off(removenote,0,removechan)

    def state_string(self, state):
        if state == Leap.Gesture.STATE_START:
            return "STATE_START"

        if state == Leap.Gesture.STATE_UPDATE:
            return "STATE_UPDATE"

        if state == Leap.Gesture.STATE_STOP:
            return "STATE_STOP"

        if state == Leap.Gesture.STATE_INVALID:
            return "STATE_INVALID"


class SampleListener(Leap.Listener):
    def on_init(self, controller):
        print "Initialized"

    def on_connect(self, controller):
        print "Connected"

        # Enable gestures
        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);
        controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

    def on_disconnect(self, controller):
        # Note: not dispatched when running in a debugger.
        print "Disconnected"

    def on_exit(self, controller):
        for idx in range(128):
            Listnr.midi.note_off(idx,0,0)
        for idx in range(128):
            Listnr.midi.note_off(idx,0,1)
        pygame.midi.quit()
        print "Exited"

    def on_frame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame()

        print "Frame id: %d, timestamp: %d, hands: %d, fingers: %d, tools: %d, gestures: %d" % (
              frame.id, frame.timestamp, len(frame.hands), len(frame.fingers), len(frame.tools), len(frame.gestures()))

        if not frame.hands.empty:
            # Get the first hand
            hand = frame.hands[0]

            # Check if the hand has any fingers
            fingers = hand.fingers
            if not fingers.empty:
                # Calculate the hand's average finger tip position
                avg_pos = Leap.Vector()
                for finger in fingers:
                    avg_pos += finger.tip_position
                avg_pos /= len(fingers)
                print "Hand has %d fingers, average finger tip position: %s" % (
                      len(fingers), avg_pos)

            # Get the hand's sphere radius and palm position
            print "Hand sphere radius: %f mm, palm position: %s" % (
                  hand.sphere_radius, hand.palm_position)

            # Get the hand's normal vector and direction
            normal = hand.palm_normal
            direction = hand.direction

            # Calculate the hand's pitch, roll, and yaw angles
            print "Hand pitch: %f degrees, roll: %f degrees, yaw: %f degrees" % (
                direction.pitch * Leap.RAD_TO_DEG,
                normal.roll * Leap.RAD_TO_DEG,
                direction.yaw * Leap.RAD_TO_DEG)

            # Gestures
            for gesture in frame.gestures():
                if gesture.type == Leap.Gesture.TYPE_CIRCLE:
                    circle = CircleGesture(gesture)

                    # Determine clock direction using the angle between the pointable and the circle normal
                    if circle.pointable.direction.angle_to(circle.normal) <= Leap.PI/4:
                        clockwiseness = "clockwise"
                    else:
                        clockwiseness = "counterclockwise"

                    # Calculate the angle swept since the last frame
                    swept_angle = 0
                    if circle.state != Leap.Gesture.STATE_START:
                        previous_update = CircleGesture(controller.frame(1).gesture(circle.id))
                        swept_angle =  (circle.progress - previous_update.progress) * 2 * Leap.PI

                    print "Circle id: %d, %s, progress: %f, radius: %f, angle: %f degrees, %s" % (
                            gesture.id, self.state_string(gesture.state),
                            circle.progress, circle.radius, swept_angle * Leap.RAD_TO_DEG, clockwiseness)

                if gesture.type == Leap.Gesture.TYPE_SWIPE:
                    swipe = SwipeGesture(gesture)
                    print "Swipe id: %d, state: %s, position: %s, direction: %s, speed: %f" % (
                            gesture.id, self.state_string(gesture.state),
                            swipe.position, swipe.direction, swipe.speed)

                if gesture.type == Leap.Gesture.TYPE_KEY_TAP:
                    keytap = KeyTapGesture(gesture)
                    print "Key Tap id: %d, %s, position: %s, direction: %s" % (
                            gesture.id, self.state_string(gesture.state),
                            keytap.position, keytap.direction )

                if gesture.type == Leap.Gesture.TYPE_SCREEN_TAP:
                    screentap = ScreenTapGesture(gesture)
                    print "Screen Tap id: %d, %s, position: %s, direction: %s" % (
                            gesture.id, self.state_string(gesture.state),
                            screentap.position, screentap.direction )

        if not (frame.hands.empty and frame.gestures().empty):
            print ""

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
        Listnr.midi.note_off(idx,0,0)
    for idx in range(128):
        Listnr.midi.note_off(idx,0,1)
    os._exit(1)

    # Remove the sample listener when done
    pygame.midi.quit()
    controller.remove_listener(listener)
    

if __name__ == "__main__":
    main()
