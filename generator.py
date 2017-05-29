from mido import MidiFile, Message
from random import random, randint, sample
from collections import deque
from parser import Parser


# generates and returns object from list template[position] with response to their weight
# if there is no position in template return random object from given sample_set
# template[position] is of type [(object, weight)]
def generate(template, position, sample_set):
    if position not in template:
        if len(sample_set) > 0:
            return sample(sample_set, 1)[0]
    if len(template[position]) == 1:
        return template[position][0][0]
    template = template[position]
    r = random()
    res = [template[i][0] for i in range(len(template) - 1) if template[i][1] > r > template[i + 1][1]]
    if res:
        return res[0]
    else:
        return sample(sample_set, 1)[0]


# transform given dictionary of type {key1 : {key2 : number }} to rand_template of type {key1 : [(key2, weight)]}
# where weight is proportionately scaled
def dictionary_to_rand_template(dictionary):

    rand_template = {}
    for i in dictionary:
        s = sum([dictionary[i][j] for j in dictionary[i]])
        tmp = [(j, dictionary[i][j] / s) for j in dictionary[i] if s != 0]
        rand_template[i] = sorted(tmp, key=lambda x: x[1], reverse=True)

        for j in reversed(range(len(rand_template[i])-1)):
            rand_template[i][j] = (rand_template[i][j][0], rand_template[i][j][1] + rand_template[i][j+1][1])

    return rand_template


class Generator:

    def __init__(self, filename, octaves, **kwargs):

        self.midi = MidiFile(filename)
        self.n = octaves*12         # used to scale notes to choosen number of octaves
        self.buffer = deque([])     # buffer for generated midi-messages
        self._parse_midi_file()

    def _parse_midi_file(self):
        # parse midiFile and swap note_on with 0 velocity to note_off to unify further steps
        for track in self.midi.tracks:
            for i in range(len(track)):
                if track[i].type == "note_on" and track[i].velocity == 0:
                    track[i] = Message(type="note_off", note=track[i].note,
                                       velocity=track[i].velocity, time=track[i].time)
        # remove meta- and change_tempo- messages
        self._notes = [x for track in self.midi.tracks for x in track if x.type == "note_on" or x.type == "note_off"]

    def generate_message(self, prev, **kwargs):
        # randomly chooses note_on message from file,
        # searches for nearest note_off message and fill the buffer with them,
        # returns first message from buffer
        fixed_note = kwargs.get('fixed_note', False)
        fixed_velocity = kwargs.get('fixed_velocity', False)
        fixed_duration = kwargs.get('fixed_duration', False)

        if not self.buffer:
            r = randint(0, len(self._notes)-1)
            while self._notes[r].type != "note_on":
                r = randint(0, len(self._notes) - 1)

            self._notes[r].velocity = fixed_velocity if fixed_velocity else self._notes[r].velocity
            self._notes[r].note = fixed_note if fixed_note else self._notes[r].note
            self._notes[r].time = 0 if fixed_duration else self._notes[r].time

            self.buffer.append(self._notes[r])
            note = self._notes[r].note

            if not fixed_note:
                while self._notes[r].note != note or self._notes[r].type == "note_on":
                    r += 1

            self._notes[r].velocity = fixed_velocity if fixed_velocity else self._notes[r].velocity
            self._notes[r].time = fixed_duration if fixed_duration else self._notes[r].time

            self.buffer.append(self._notes[r])

        return self.buffer.popleft()


class MCGenerator(Generator):

    def __init__(self, filename, octaves, **kwargs):
        Generator.__init__(self, filename, octaves)

    # parse midi-file and prepare markov_chain with respect to single notes as matrix,
    # then transform it to rand_template
    # count velocity and time values probability connected to each note
    def _parse_midi_file(self):

        Generator._parse_midi_file(self)
       # self.matrix = [[0] * self.n] * self.n
        self.matrix = [[0 for x in range(self.n+1)] for y in range(self.n+1)]

        on_velocity = {}
        off_velocity = {}
        on_time = {}
        off_time = {}

        self.note_sample = set()
        self.velocity_sample = set()
        self.time_sample = set()

        for i in range(len(self._notes)-1):
            self.matrix[self._notes[i].note % self.n][self._notes[i+1].note % self.n] += 1
            self.note_sample.add(self._notes[i].note % self.n)

        self.rand_note_template = self._note_rand_template(self.n)

        for i in self._notes:

            def process(dictionary, n, value):

                if n in dictionary and value in dictionary[n]:
                    dictionary[n][value] += 1

                else:
                    if n not in dictionary:
                        dictionary[n] = {}
                    dictionary[n][value] = 1

            note = i.note % self.n

            if i.type == "note_on":
                process(on_velocity, note, i.velocity)
                process(on_time, note, i.time)

            else:
                process(off_velocity, note, i.velocity)
                process(off_time, note, i.time)
            self.velocity_sample.add(i.velocity)
            self.time_sample.add(i.time)

        self.on_velocity = dictionary_to_rand_template(on_velocity)
        self.on_time = dictionary_to_rand_template(on_time)
        self.off_velocity = dictionary_to_rand_template(off_velocity)
        self.off_time = dictionary_to_rand_template(off_time)

    # prepare rand_template of notes from generator's matrix od coincidence
    def _note_rand_template(self, max_v):

        for i in range(max_v):
            s = sum([x for x in self.matrix[i]])
            if s != 0:
                self.matrix[i] = [x/s for x in self.matrix[i]]
            else:
                self.matrix[i] = [0 for x in self.matrix[i]]

        rand_template = [None]*max_v
        for i in range(max_v):
            rand_template[i] = [(j, self.matrix[i][j]) for j in range(max_v)]
            rand_template[i] = sorted(rand_template[i], key=lambda y: y[1], reverse=True)
            for z in reversed(range(max_v - 1)):
                rand_template[i][z] = (rand_template[i][z][0], rand_template[i][z][1] + rand_template[i][z + 1][1])

        return rand_template

    # generates messages using prepared templates and fill them in buffer
    # if messages features were chosen to be fixed set them respectively
    def generate_message(self, prev, **kwargs):

        fixed_duration = kwargs.get('fixed_duration', False)
        fixed_note = kwargs.get('fixed_note', False)
        fixed_velocity = kwargs.get('fixed_velocity', False)

        if not self.buffer:

            note = generate(self.rand_note_template, prev.note % self.n, self.note_sample)
            real_note = int(int((note+12) / 12) * (120 / (self.n / 12 + 1)) + note % 12)
            velocity = generate(self.on_velocity, note, self.velocity_sample)
            time = generate(self.on_time, note, self.time_sample)

            real_note = fixed_note if fixed_note else real_note
            velocity = fixed_velocity if fixed_velocity else velocity
            time = 0 if fixed_duration else time

            self.buffer.append(Message(type="note_on", note=real_note, velocity=velocity, time=time))

            velocity = generate(self.off_velocity, note, self.velocity_sample)
            time = generate(self.off_time, note, self.time_sample)
            if time == 0:
                time = 250

            velocity = fixed_velocity if fixed_velocity else velocity
            time = fixed_duration if fixed_duration else time

            self.buffer.append(Message(type="note_off", note=real_note, velocity=velocity, time=time))

        return self.buffer.popleft()


class ChordMCGenerator(Generator):

    def __init__(self, filename, **kwargs):

        Generator.__init__(self, filename, 10)

        parser = Parser(self.midi, 4, kwargs.get('with_duration', False))

        self.rand_template = dictionary_to_rand_template(parser.matrix)

        self.messages_dictionary = parser.messages_dictionary
        self.notes_sample = parser.notes_sample
        self.prev = sample(self.notes_sample, 1)[0]

    # generate messages using templates returned by parser, fill them in buffer
    def generate_message(self, **kwargs):
        if not self.buffer:
            note = generate(self.rand_template, self.prev, self.notes_sample)
            self.buffer.extend(self.messages_dictionary[note][0])
            self.buffer.extend(self.messages_dictionary[note][1])
            self.prev = note
        return self.buffer.popleft()
