#!/usr/bin/env python
#
# mp3 file of song vocals ripped from this video posted by Rhye cl: https://www.youtube.com/watch?v=2GGFdY3Sopc
#
songfile='queen.show.mp3'
strictharmony_left=1.0
strictharmony_right=1.0
timedelay=1.0 # Time (seconds) to wait for the external song before chord sequence starts
songvolume=0.8
bpm=60
#time1=30.97 # Chord 1, "Empty sp-aces" cambio a Amin
#time2=3*60.+56.618 # Chord 74, "...on with the show"... cambio a Dmi5- (E min)
#bpm=(74.-1.)*4./((time2-time1)/60.)
#bartimes=[x*60./bpm*4. for x in range(len(chords2play))]

tuneshift=2 # Shift all notes by this many half-tones

chords2play= ['A min', 'A min', 'A min', 'F ', 'F ', 'D min7', 'D min7', 'E sus4', 'E ', 'D min', 'D min7', 'A min', 'A min', 'F ', 'F ', 'D min7', 'D min7', 'E sus4', 'E ', 'D min', 'A min', 'A min', 'F ', 'F ', 'D min7', 'D min7', 'E sus4', 'E ', 'D min', 'D min7', 'A min', 'A min', 'B min', 'B min', 'G ', 'G ', 'E min7', 'E min6', 'F#sus4', 'F#', 'E min', 'E min7', 'B min', 'B min', 'G ', 'G ', 'E min7', 'E min6', 'F#sus4', 'F#', 'E min', 'E min7', 'D min', 'A min', 'A min', 'F ', 'F ', 'D min7', 'D min7', 'E sus4', 'E ', 'D min', 'D min7', 'A min', 'A min', 'F ', 'F ', 'D min7', 'D min7', 'E sus4', 'E ', 'D min', 'D min7', 'D#', 'F ', 'D min', 'G min', 'D#', 'F ', 'D min', 'G min', 'G 9', 'C ', 'A min', 'A min', 'F ', 'F ', 'D min7', 'D min7', 'E sus4', 'E ', 'D min', 'A min', 'A min', 'F ', 'F ', 'D min7', 'D min7', 'E sus4', 'E ', 'D min', 'D min7', 'D min', 'A min',
             'A min','A min',
             'A min','A min','A min','A min','A min']

bartimes=[0.0,2.533916,5.259754,8.145974,11.074259,13.904522,15.305486,16.767951,18.191854,19.613805,21.043787,22.39159,25.296849,28.1851,31.042223,33.899382,35.40739,36.749832,38.452647,39.67957,42.38289,46.788196,48.158804,52.425072,53.884473,56.173917,56.697277,58.222756,59.539141,60.981626,62.324943,65.357807,68.082607,70.926903,73.718021,76.771667,79.47994,81.418602,82.415361,84.391472,85.286992,87.269014,88.095119,90.853685,93.691893,96.580328,99.495682,100.914349,102.355663,103.900849,105.393979,107.254566,109.367109,110.926674,115.22507,116.726141,119.477252,122.370006,124.660673,125.326094,127.279175,128.218932,130.08445,130.889897,133.746921,136.620955,140.065846,141.529712,143.097537,145.837099,147.440506,148.735401,150.288588,151.69717,153.329244,154.572879,155.825705,157.272017,158.693455,160.219647,161.675917,163.05136,164.529705,165.892459,170.104829,174.441056,177.287831,180.174833,182.090808,183.024531,184.830904,186.016432,188.748107,191.607597,194.37595,197.26714,200.136571,201.674509,203.164508,204.704994,206.54176,208.752472,211.394736,214.151376,217.067148,219.815456,221.204235,222.480935,222.918065,223.226339,223.495976,223.788555]

