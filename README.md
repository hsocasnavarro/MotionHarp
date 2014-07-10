MotionHarp
==========

MOTION HARP: Music with a 3D interface using the Leap Motion
hsocas.iac@gmail.com

(2014) Hector Socas-Navarro: MOTION HARP
Requirements:
 * Python
 * pygame
 * LeapMotion SDK
 * if not in your path, LeapSDK/lib/Leap.py, LeapSDK/lib/x??/LeapPython.so
      libLeap.so must be present in the running directory
 * A MIDI synthesizer. This can be a hardware device connected to your
      computer, or a software synthesizer. In Linux, you can use qsynth

Optional:
 * Optionally, run simultaneously the Leap Motion Visualizer 
      application to see how your hands are being tracked in real time
 
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
#       hand it belongs to must be reliably detected by the Leap Motion.
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

#
# COMMENTS AND NOTES:
#
#  This program does not render sound. You need a MIDI instrument
#  or software synthesizer to hear the music. Under Linux you can
#  use qsynth as a synthesizer. Once started you should see it in
#  the list of available ports shown when you start Motion Harp. 
#  If you're using qsynth it will appear as "Synth input port" in the 
#  port list. 
#
# For better coverage of the lower notes, orient the Leap Motion device
#  with the USB connnector pointing left. This will give it a better view
#  of your left hand near the leftmost edge of the detection box.
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


  
