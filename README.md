# MusicGenerator
Midi file music generating using markov chains on source midi file  for Programowanie w języku Python

usage: main.py [-h] [-source SOURCE] [-path PATH] [-length LENGTH] [-p]
               {s,n,c} ...

positional arguments:
  {s,n,c}         type of generator
    s             generates music using shuffled messages from source file
    n             generates music using markov chain of notes
    c             generates music using markov chain of chords

optional arguments:
  -h, --help      show this help message and exit
  -source SOURCE  path to source file with music to inspire
  -path PATH      path to file with generated music
  -length LENGTH  length of music generated (in number of notes_on)
  -p, -print      print generated music

shuffling generator options:
usage: main.py s [-h] [-d DURATION] [-v VELOCITY]

optional arguments:
  -h, --help            show this help message and exit
  -d DURATION, --duration DURATION
                        fixed duration of notes
  -v VELOCITY, --velocity VELOCITY, -v VELOCITY
                        fixed velocity of notes (0-127)

markov chain of notes generator options:
usage: main.py n [-h] [-o {1,2,3,4,5,6,7,8,9,10}] [-d DURATION] [-v VELOCITY]

optional arguments:
  -h, --help            show this help message and exit
  -o {1,2,3,4,5,6,7,8,9,10}, --octaves {1,2,3,4,5,6,7,8,9,10}
                        number of octaves in which generator works
  -d DURATION, --duration DURATION
                        fixed duration of notes
  -v VELOCITY, --velocity VELOCITY
                        fixed velocity of notes (0,127)

markov chain of chords generator options:
usage: main.py c [-h] [-d]

optional arguments:
  -h, --help      show this help message and exit
  -d, --duration  duration of chord is factor in building markov chain
