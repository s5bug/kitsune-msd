import logging
from math import floor

from msdparser import parse_msd
import argparse, os, re


def file_path(string):
    if os.path.isfile(string):
        return string
    else:
        raise FileNotFoundError(string)


def new_file_path(string):
    if os.path.isfile(string):
        raise FileExistsError(string)
    elif os.path.isdir(os.path.dirname(os.path.realpath(string))):
        return string
    else:
        raise NotADirectoryError(os.path.dirname(os.path.realpath(string)))


remove_all_whitespace = re.compile(r'\s+')


def raw_notedata(notedata):
    return re.sub(remove_all_whitespace, '', notedata).split(':')


def raw_measuredata(notedata):
    return notedata.split(',')


def note_count(measuredata):
    unfloored = len(measuredata) / 4
    if unfloored == floor(unfloored):
        return floor(unfloored)
    else:
        raise ArithmeticError("Some measure is not divisible by 4!")


def note_types(note):
    return [i for i in range(len(note)) if note[i] == "1"]


def write_note_datas(offset, jsonfile, metadata, measures):
    bpm_map = dict([ent.split('=') for ent in metadata["BPMS"].split(',')])
    if len(bpm_map) != 1:
        logging.warning("Can't yet handle a song with multiple BPMs")
        return

    bpm = float(bpm_map["0.000"])
    time_per_beat = 60.0 / bpm

    time_now = float(metadata["OFFSET"]) + offset
    jsonfile.write("[")
    for measure in measures:
        nc = note_count(measure)
        time_per_note = time_per_beat * (4.0 / nc)
        for note_num in range(nc):
            for note_type in note_types(measure[(4 * note_num):(4 * (note_num + 1))]):
                jsonfile.write("{\"type\":")
                jsonfile.write(str(note_type))
                jsonfile.write(",\"time\":")
                jsonfile.write(str(time_now * 1000.0))
                jsonfile.write("},")
            time_now += time_per_note
    # write kill note
    jsonfile.write("{\"type\":10,\"time\":")
    jsonfile.write(str(time_now * 1000.0))
    jsonfile.write("}]")


parser = argparse.ArgumentParser(description='Convert a StepMania file into a Champion Island Games Swimming file.')
parser.add_argument('input', type=file_path, help='the input .sm file')
parser.add_argument('output', type=new_file_path, help='the output .json file')
parser.add_argument('--offset', type=float, default=0.000, help='offset of song data in seconds')


def main():
    args = parser.parse_args()
    output_dir = os.path.dirname(os.path.realpath(args.output))
    output_name = os.path.basename(os.path.realpath(args.output))
    with open(args.input, 'r', encoding='utf-8') as smfile:
        msd_file = list(parse_msd(file=smfile))
        metadata = dict([(x, y) for (x, y) in msd_file if x != "NOTES"])
        notedata = list([y for (x, y) in msd_file if x == "NOTES"])
        for track in notedata:
            song_type, author, difficulty, meter, groove, raw = raw_notedata(track)
            if song_type == "dance-single":
                measures = raw_measuredata(raw)
                output_path = os.path.join(output_dir, f'{difficulty}-{output_name}')
                with open(output_path, 'w', encoding='utf-8') as jsonfile:
                    write_note_datas(args.offset, jsonfile, metadata, measures)
            else:
                logging.warning(f'Unhandleable track with song_type of {song_type}')


if __name__ == '__main__':
    main()
