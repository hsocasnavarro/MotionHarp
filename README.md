MotionHarp
==========

MOTION HARP: Music with a 3D interface using Linux, Python and the Leap Motion

(2013) Hector Socas Navarro: MOTION HARP
Requirements:
 * Python
 * pygame
 * LeapMotion SDK
 * if not in your path, LeapSDK/lib/Leap.py and LeapSDK/lib/x??/LeapPython.so
      must be present in the running directory
 * OPTIONAL. If you have xdotool then the mouse pointer will show
      the notes played

# Instructions:

   * Notes are triggered when a finger moves down and released when it moves up.
   * A finger is locked and may not trigger another note until one of the
      following conditions are met:
       a)It moves up again
       b)0.5 seconds from the last note have passed
       c)All locks are released (see below)
   * If a hand moves fast in the horizontal direction, all locks are
      released and remain that way for the next 2 seconds, allowing 
      for quick note bursts.
   * The notes triggered are picked randomly from the current chord, 
      except for the free-style mode described below. The octave is
   *  determined by the position of the finger in the left-right direction
   * The current chord is changed by moving hands forward or backward
   * The height of the hand that plays a note determines its volume
   * If the hand is higher than 250 mm, then notes are not bound to 
      current chord any more allowing for a more free-style playing.
      However, not every note is permitted even in this mode to avoid
      dissonances. Only notes from the current key are played
   * Showing a hand with the palm facing up brings up the strings.
      When strings are on they always play the first note in the
      current chord. The hand may still be moved to change
      chord and therefore the string note without playing piano notes.
      However, even with the palm facing up, vertical finger movement
      will trigger piano notes

  NOTE: This program does not render sound. You need a MIDI instrument
  or software synthesizer to hear the music. Under Linux you can
  use e.g. qsynth as a synthesizer. Once started you should see it in
  the list of available ports shown when you start Motion Harp. 
  If you're using qsynth it will appear as "Synth input port" in the 
  port list. 

