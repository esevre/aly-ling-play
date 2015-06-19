# from __builtin__ import open, len, int, unicode, object
import os, codecs

__author__ = 'esevre'


#
#  When we expect that the next line should be a linenumber, use this method
#
def read_next_line_for_linenumber(file):
    line = file.readline().split()
    if len(line) == 0:
        # Empty Line, so try the next line
        return read_next_line_for_linenumber(file)
    elif len(line) == 1:
        if unicode(line[0], 'utf-8').isnumeric():
            return int(line[0])
        else:
            print('the line number should be numeric, but is not. Only integer line numbers are accepted')
            return -1
    else:
        print('the line contains too much information, should only contain a line number')
        return -1

#
#  When we expect that the next line should be a timestamp, use this method
#
def read_next_line_for_timestamps(file):
    line = file.readline().split()
    if len(line) != 3:
        print('This is an unsuported srt file type')
        return -1
    assert line[1] == '-->'  # this should be the second part of each line
    # print 'timestamp line:', line
    start_time = TimeStamp(line[0])
    stop_time = TimeStamp(line[2])
    return [start_time, stop_time]

#
#  When we expect that the next line(s) should be a subtitles, use this method
#
def read_lines_for_subtitles(file):
    lines = []
    line = file.readline()  # don't split this line
    while len(line) != 1:
        lines.append(line)
        line = file.readline()
    return lines


#
#  This object is used to hold the SRT Entry information.
#
#  Here a SRT Entry consists of a linenumber, timestamp, and subtitle line(s)
#
#  And a SRT file would have many SRT Entries in it
#
class SRTEntry(object):
    line_number = 0
    start_time = 0
    stop_time = 0
    subtitle_lines = []

    #
    #  This init method is complex, because I want to allow multiple ways to init the SRTEntry object
    #
    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            foundOneArg = True; theOnlyArg = args[0]
        else:
            foundOneArg = False; theOnlyArg = None

        if foundOneArg and isinstance(theOnlyArg, type([])):
            self.init_from_list(theOnlyArg)
        elif foundOneArg and isinstance(theOnlyArg, file):
            self.init_from_filestream(theOnlyArg)
            print('init with one arg')
        elif len(args) > 1:
            self.init_from_args(*args)
        elif len(args) == 0:
            self.init_empty()
            print('init empty')

    def init_from_filestream(self, source):
        if type(source) == file:
            self.line_number = read_next_line_for_linenumber(source)
            self.start_time, self.stop_time = read_next_line_for_timestamps(source)
            self.subtitle_lines = read_lines_for_subtitles(source)
        else:
            self.__init__()

    def init_empty(self):
        self.line_number = 0
        self.start_time = TimeStamp()
        self.stop_time = TimeStamp()
        self.subtitle_lines = []

    def init_from_args(self, *args):
        if len(*args) == 4:
            line_number = args[0]
            start_time = args[1]
            stop_time = args[2]
            subtitles = args[3]

    def init_from_list(self, param_list):
        self.line_number = param_list[0]
        self.start_time = param_list[1]
        self.stop_time = param_list[2]
        self.subtitle_lines = param_list[3]

    def to_string(self):
        line_number_string = '%d\n' % self.line_number
        time_stamp_string = '%s --> %s\n' % (self.start_time.to_string(), self.stop_time.to_string())
        subtitle_string = ''
        for sub in self.subtitle_lines:
            subtitle_string = subtitle_string + sub + '\n'
        return line_number_string + time_stamp_string + subtitle_string


class TimeStamp(object):
    hours = 0
    minutes = 0
    seconds = 0
    milliseconds = 0

    def __init__(self, *args, **kwargs):
        if len(args) == 0:
            self.init_empty()
        if len(args) == 1:
            self.init_from_string(args[0])

    def init_empty(self):
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.milliseconds = 0

    def init_from_string(self, time_string):
        assert check_timestamp_format(time_string)
        hour_min_sec = time_string.split(':')
        self.hour = int(hour_min_sec[0])
        self.minutes = int(hour_min_sec[1])
        sec_millisec = hour_min_sec[2].split(',')
        self.seconds = int(sec_millisec[0])
        self.milliseconds = int(sec_millisec[1])

    def to_string(self):
        return '%02d:%02d:%02d,%03d' % (self.hours, self.minutes, self.seconds, self.milliseconds)


#  This method checks that the timestamp has a valid format
#
#  Input for timestamp is a string representation of a timestamp
#
# timestamp should have the format:
#  01 34 67 901
#  NN:NN:NN,NNN
def check_timestamp_format(timestamp):
    numeric_bits = [0, 1, 3, 4, 6, 7, 9, 10, 11]
    colon_bits = [2, 5]
    comma_bits = [8]
    for i in numeric_bits:
        if not timestamp[i].isnumeric():
            print('problem with timestamp format')
            return False
    for i in colon_bits:
        if timestamp[i] != ':':
            print('problem with timestamp format')
            return False
    for i in comma_bits:
        if timestamp[i] != ',':
            print('problem with timestamp format')
            return False
    return True


def srt_list_from_file(filename):
    _file = open(filename, 'r')  # Open File
    _file_data = _file.read()  # Read in the file
    _file.close()  # Close File

    #
    #  There were some problems with some kind of BOM in the file so the first character may need to be removed
    #  (BOM - Byte Order Mark)
    if not _file_data[0].isalnum():
        _file_data = _file_data[1:]

    _srt_list = []  # empty list to hold SRT data from the file
    _file_lines = _file_data.split('\n')  # Split file by lines

    _line_number = 0
    _start_time = 0
    _stop_time = 0
    _subtitles = []
    _last_line = ''
    _global_line_number = 0
    for line in _file_lines:
        _global_line_number += 1
        # Check for the kind of line, if last_line = '', then there should be a new entry
        #
        #  If _last_line is empty then we should start a new srt
        #
        #  Later I should add some checks for multiple blank lines
        if _last_line == '':
            if line != '':
                line_strip = line.strip()
                assert line_strip.isdigit(), \
                    '\nIn file: %s, line: %s \n\tProblem with SRT input file, \n\tline number expected recieved: %s' \
                    % (filename, _global_line_number, line)
                _line_number = int(line)
                _last_line = 'number'
        # If the last line is a number, then the next line should be start-stop time
        elif _last_line == 'number':
            _start_0_stop = line.split()
            assert _start_0_stop[1] == '-->'
            _start_time = TimeStamp(_start_0_stop[0])
            _stop_time = TimeStamp(_start_0_stop[2])
            _last_line = 'timestamp'
        # if the last line is a timestamp, the next line is the subtitle
        elif _last_line == 'timestamp' or _last_line == 'subtitles':
            if len(line) == 0:
                if _last_line == 'subtitles':
                    # print 'adding an srt entry'
                    input = [_line_number, _start_time, _stop_time, _subtitles]
                    _srt = SRTEntry(input)
                    _srt_list.append(_srt)
                    _subtitles = []
                _last_line = ''
            else:
                _subtitles.append(line)
                _last_line = 'subtitles'
    if _last_line == \
            'subtitles':
        input = [_line_number, _start_time, _stop_time, _subtitles]
        _srt = SRTEntry(input)
        _srt_list.append(_srt)

    return _srt_list


#
#  This will read all the SRT Files, and generate a txt file for each srt file.
# The txt file will be the raw text of the conversation from the SRT files.
#
# So for the directory given, if you have 'file1.srt', 'another.srt', then it will
#   create text files 'file1.txt' and 'another.txt'
#
def process_files_in_directory(directory_path):
    srt_extension = '.srt'

    allfiles = os.listdir(directory_path)

    files_to_process = []
    for a_file in allfiles:
        if a_file[-4:] == srt_extension:  # check that the extension is .srt
            files_to_process.append(a_file)

    all_text_from_files = ''
    for filename in files_to_process:
        srt_list = srt_list_from_file(filename)
        current_file_text = ''
        current_filename_base = filename[:-4]
        for srt in srt_list:
            for line in srt.subtitle_lines:
                current_file_text = current_file_text + line + '\n'
        all_text_from_files = all_text_from_files + current_file_text + '\n'
        write_file = current_filename_base + '.txt'
        print ('writing file: ', write_file)
        output_file = open(write_file, 'w')
        output_file.write(current_file_text)
        output_file.close()

    output_file = open('all_files.txt', 'w')
    output_file.write(all_text_from_files)
    output_file.close()

#
#  This will read SRT files and convert them to TXT files and allow for that in two directories
#
def process_files_in_two_directory(srt_path, txt_path):
    srt_extension = '.srt'

    if srt_path[-1] != '/':
        srt_path += '/'
    allfiles = os.listdir(srt_path)

    files_to_process = []
    for a_file in allfiles:
        if a_file[-4:] == srt_extension:  # check that the extension is .srt
            files_to_process.append(a_file)

    all_text_from_files = ''
    for filename in files_to_process:
        srt_list = srt_list_from_file(srt_path + filename)
        current_file_text = ''
        current_filename_base = filename[:-4]
        for srt in srt_list:
            for line in srt.subtitle_lines:
                current_file_text = current_file_text + line + '\n'
        all_text_from_files = all_text_from_files + current_file_text + '\n'

        write_file = current_filename_base + '.txt'
        if txt_path[-1] != '/':
            txt_path += '/'
        write_file = txt_path + write_file

        print ('writing file: ', write_file)
        output_file = open(write_file, 'w')
        output_file.write(current_file_text)
        output_file.close()

    output_file = open('all_files.txt', 'w')
    output_file.write(all_text_from_files)
    output_file.close()

####    ####    ####    ####    ####    ####
##
##   Code to edit is below here
##
##
##  this will only run if we run this as the main program
##  so if we import this into another file it won't run
##
####    ####    ####    ####    ####    ####

if __name__ == "__main__":
    process_files_in_two_directory('srt', 'txt')
