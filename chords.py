#!/usr/bin/env python

notes=['C ','C#','D ','D#','E ','F ','F#','G ','G#','A ','A#','B ']
semitones={'C ':0,'C#':1,'D ':2,'D#':3,'E ':4,'F ':5,'F#':6,'G ':7,'G#':8,'A ':9
,'A#':10,'B ':11}
ChordKeys={'C ':['G ', 'C ', 'E '], 'C maj':['G ', 'C ', 'E ', 'B '], 'C min':['G ', 'C ', 'D#'], 'C#':['G#', 'C#', 'F '], 'C#maj':['G#', 'C#', 'F ', 'C '], 'C#min':['G#', 'C#', 'E '], 'D ':['A ', 'D ', 'F#'], 'D maj':['A ', 'D ', 'F#', 'C#'], 'D min':['A ', 'D ', 'F '], 'D#':['A#', 'D#', 'G '], 'D#maj':['A#', 'D#', 'G ', 'D '], 'D#min':['A#', 'D#', 'F#'], 'E ':['B ', 'E ', 'G#'], 'E maj':['B ', 'E ', 'G#', 'D#'], 'E min':['B ', 'E ', 'G '], 'F ':['C ', 'F ', 'A '], 'F maj':['C ', 'F ', 'A ', 'E '], 'F min':['C ', 'F ', 'G#'], 'F#':['C#', 'F#', 'A#'], 'F#maj':['C#', 'F#', 'A#', 'F '], 'F#min':['C#', 'F#', 'A '], 'G ':['D ', 'G ', 'B '], 'G maj':['D ', 'G ', 'B ', 'F#'], 'G min':['D ', 'G ', 'A#'], 'G#':['D#', 'G#', 'C '], 'G#maj':['D#', 'G#', 'C ', 'G '], 'G#min':['D#', 'G#', 'B '], 'A ':['E ', 'A ', 'C#'], 'A maj':['E ', 'A ', 'C#', 'G#'], 'A min':['E ', 'A ', 'C '], 'A#':['F ', 'A#', 'D '], 'A#maj':['F ', 'A#', 'D ', 'A '], 'A#min':['F ', 'A#', 'C#'], 'B ':['F#', 'B ', 'D#'], 'B maj':['F#', 'B ', 'D#', 'A#'], 'B min':['F#', 'B ', 'D '], }

def rotating_idx(mylist,idx):
    l=len(mylist)
    idx2=idx%l
    return mylist[idx2]
