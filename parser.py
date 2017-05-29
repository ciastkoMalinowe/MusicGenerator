from mido.frozen import freeze_message


class Parser:

    def __init__(self, midi, max_piece_length, with_duration=False):
        self.midi = midi
        self.with_duration = with_duration
        self.notes_sample = set()
        self.max_piece_len = max_piece_length
        self.matrix = {}

        # dictionary  key=frozenset(notes) value=([notes_on messages],[notes_off messages])
        self.messages_dictionary = {}
        self._parse()

    def _parse(self):

        default_tempo = 500000
        default_ticks_per_beat = 240
        current_tempo = 500000
        remembered_notes = {}

        # dictionary with single notes waiting to be offed {key : (time of waiting, message)}
        waiting = {}

        # seed to generate next midi-messages (of type (frozenset(notes), duration) )
        prev = (frozenset({60}), 20)
        piece_of_music_prev = (frozenset({60}), 20)

        # set of notes to be treat as one (noted on but not yet off)
        piece_of_music = set()

        # set of (note_on message, note_off message) notes waited in from piece_of_music
        current_set = set()
        time = 0

        # counts current duration of note with respect to current tempo and ticks per beat
        # if generator not care about note duration returns 0
        def duration(t):
            if self.with_duration:
                return int((t * current_tempo / self.midi.ticks_per_beat)/25000)
            return 0

        def update_waiting(t):
            for i in waiting:
                waiting[i] = (waiting[i][0] + t, waiting[i][1])

        # update time in given message with respect to current tempo and default setting of generating file
        def update_tempo(mes):
            mes.time = mes.time * current_tempo / self.midi.ticks_per_beat
            mes.time = mes.time * default_ticks_per_beat / default_tempo
            mes.time = int(mes.time)
            return mes

        for track in self.midi.tracks:
            for message in track:
                message = update_tempo(message)

                if message.type == "set tempo":
                    time += message.time
                    update_waiting(message.time)
                    current_tempo = message.tempo

                if message.type == "note_on":
                    time += message.time
                    update_waiting(message.time)
                    if message.time == 0 or message.note not in piece_of_music \
                            or len(piece_of_music)+len(current_set) < self.max_piece_len:
                        if not piece_of_music:
                            time = 0
                            piece_of_music_prev = prev
                        piece_of_music.add(message.note)
                        remembered_notes[message.note] = freeze_message(message)
                    else:
                        waiting[message.note] = (0, freeze_message(message))

                if message.type == "note_off":
                    time += message.time
                    update_waiting(message.time)
                    if message.note in piece_of_music:  # one note from chord ends
                        current_set.add((remembered_notes[message.note], freeze_message(message)))
                        piece_of_music.remove(message.note)
                        if not piece_of_music:  # if so it was last note from note
                            notes_set = self._add_to_messages_dictionary(current_set, duration(time))
                            next_note = (notes_set, duration(time))
                            self._add_to_matrix(piece_of_music_prev, next_note)
                            prev = next_note
                            current_set.clear()
                            time = 0
                    elif message.note in waiting:
                        note_on = waiting[message.note]
                        f = frozenset({message.note})
                        self.messages_dictionary[(f, duration(note_on[0]))] = ([note_on[1]], [freeze_message(message)])
                        self._add_to_matrix(prev, (f, duration(note_on[0])))
                        prev = (f, duration(note_on[0]))
                        waiting.pop(message.note)

    # adds messages generating chord to dictionary frozenset(notes) : (note_on messages, note_off messages)
    def _add_to_messages_dictionary(self, set_to_add, t):
        s = set()
        l_on = []
        l_off = []
        for i in set_to_add:
            s.add(i[0].note)
            l_on.append(i[0])
            l_off.append(i[1])

        f = frozenset(s)
        if f not in self.messages_dictionary:
            self.messages_dictionary[(f, t)] = (l_on, l_off)
        return f

    def _add_to_matrix(self, a, b):
        if a in self.matrix and b in self.matrix[a]:
            self.matrix[a][b] += 1
        else:
            if a not in self.matrix:
                self.matrix[a] = {}
            self.matrix[a][b] = 1
        self.notes_sample.add(b)
