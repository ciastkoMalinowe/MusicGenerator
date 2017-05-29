from mido import MidiFile, MidiTrack, Message
from random import randint
from generator import MCGenerator, ChordMCGenerator, Generator
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-source", help="path to source file with music to inspire",
                    type=str)
parser.add_argument("-path", help="path to file with generated music",
                    type=str)
parser.add_argument("-length", help="length of music generated (in number of notes_on)",
                    type=int)
parser.add_argument("-p", "-print", action='store_true', help="print generated music")
parser.set_defaults(generator=MCGenerator, path="result.mid", length=500,
                    source="./sources/november_rain.mid", print=False,
                    octaves=10, duration=False, velocity=False)

subparsers = parser.add_subparsers(help='type of generator')

parser_shuffle = subparsers.add_parser('s', help='generates music using shuffled messages from source file')
parser_shuffle.add_argument("-d", "--duration", help="fixed duration of notes",
                            type=int)
parser_shuffle.add_argument("-v", "--velocity", "-v", help="fixed velocity of notes (0-127)",
                            type=int)
parser_shuffle.set_defaults(generator=Generator, octaves=10, duration=False, velocity=False)

parser_markov = subparsers.add_parser('n', help='generates music using markov chain of notes')
parser_markov.add_argument("-o", "--octaves", help="number of octaves in which generator works",
                           type=int, choices=range(1, 11))
parser_markov.add_argument("-d", "--duration", help="fixed duration of notes",
                           type=int)
parser_markov.add_argument("-v", "--velocity", help="fixed velocity of notes (0,127)",
                           type=int)
parser_markov.set_defaults(generator=MCGenerator, octaves=10, duration=False, velocity=False)


parser_chord_markov = subparsers.add_parser('c', help='generates music using markov chain of chords')
parser_chord_markov.add_argument("-d", "--duration", action='store_true',
                                 help="duration of chord is factor in building markov chain")
parser_chord_markov.set_defaults(generator=ChordMCGenerator, octaves=10, duration=False, velocity=False)

args = parser.parse_args()

try:
    mid = MidiFile(args.source)
except FileNotFoundError:
    print("Source file not exists :(")
    exit()

result = MidiFile()
track = MidiTrack()
result.tracks.append(track)

prev_note = randint(0, 11)
prev_note += 60
prev = Message(type="note_on", note=prev_note, time=0)
track.append(prev)
prev = Message(type="note_off", note=prev_note, time=100)
track.append(prev)

gen = args.generator(args.source, octaves=args.octaves, with_duration=args.duration)
for i in range(0, args.length):
    prev = gen.generate_message(prev=prev, fixed_duration=args.duration, fixed_velocity=args.velocity)
    track.append(prev)
    if args.p:
        print(prev)
print("Generated music saved in " + args.path)
print("Length: ", result.length, "s", sep="")
print("Try another options to custom your song")

result.save(args.path)
