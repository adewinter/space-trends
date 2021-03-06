from datetime import datetime
import pprint
import re
from os import scandir
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

import pyperclip

from spacetrends.models import Launch, Orbit, Site, Vehicle

class OrbitCodesParser():
    def __init__(self, stdout, style, filepath, filename, is_debug_mode):
        self.stdout = stdout
        self.style = style
        self.filepath = filepath
        self.filename = filename
        self.is_debug_mode = is_debug_mode #Set to `True` when passed in --verbosity flag is greater than 1

    def pprint(self, msg):
        self.stdout.write(self.style.SUCCESS(msg))

    def debug_print(self, msg):
        if self.is_debug_mode:
            self.pprint(msg)

    def debug_pprint(self, msg):
        self.debug_print(pprint.pformat(msg))

    def parse_orbit_code_entry_from_line(self, line):
        symbols = line.strip("\n").split(' = ')
        return {
            "code": symbols[0],
            "name": symbols[1]
        }

    def update_orbit_code_db_with_entry(self, entry):
        code = entry["code"].strip()
        name = entry["name"].strip()
        orbit, _ = Orbit.objects.get_or_create(code__iexact=code, defaults={'code': code})
        orbit.name = name
        orbit.save()

    def parse(self):
        self.pprint(f"Parsing Orbital Codes from File: {self.filepath}")
        with open(self.filepath, 'r') as orbit_codes_file:
            orbit_code_lines = orbit_codes_file.readlines()

        count = 0
        for orbit_code_line in orbit_code_lines:
            orbit_code_entry = self.parse_orbit_code_entry_from_line(orbit_code_line)
            
            self.debug_pprint(f"Parsing orbit: {orbit_code_line}")
            self.debug_pprint(orbit_code_entry)
            self.debug_pprint("")

            self.update_orbit_code_db_with_entry(orbit_code_entry)
            count += 1

        self.pprint(f"Parsed {count} orbital code entries!")



class SiteCodesParser():
    def __init__(self, stdout, style, filepath, filename, is_debug_mode):
        self.stdout = stdout
        self.style = style
        self.filepath = filepath
        self.filename = filename
        self.is_debug_mode = is_debug_mode #Set to `True` when passed in --verbosity flag is greater than 1

    def pprint(self, msg):
        self.stdout.write(self.style.SUCCESS(msg))

    def debug_print(self, msg):
        if self.is_debug_mode:
            self.pprint(msg)

    def debug_pprint(self, msg):
        self.debug_print(pprint.pformat(msg))

    def parse_site_code_entry_from_line(self, line):
        symbols = line.strip("\n").split(' = ')
        return {
            "code": symbols[0],
            "name": symbols[1]
        }

    def update_site_code_db_with_entry(self, entry):
        site, _ = Site.objects.get_or_create(code=entry["code"])
        site.name = entry["name"]
        site.save()

    def parse(self):
        self.pprint(f"Parsing Site Codes from File: {self.filepath}")
        with open(self.filepath, 'r') as site_codes_file:
            site_code_lines = site_codes_file.readlines()

        count = 0
        for site_code_line in site_code_lines:
            site_code_entry = self.parse_site_code_entry_from_line(site_code_line)
            
            self.debug_pprint(f"Parsing site: {site_code_line}")
            self.debug_pprint(site_code_entry)
            self.debug_pprint("")

            self.update_site_code_db_with_entry(site_code_entry)
            count += 1

        self.pprint(f"Parsed {count} orbital code entries!")


class LaunchNotesParser():
    def __init__(self, stdout, style, filepath, filename, is_debug_mode, notes_start_index):
        self.stdout = stdout
        self.style = style
        self.filepath = filepath
        self.filename = filename
        self.is_debug_mode = is_debug_mode #Set to `True` when passed in --verbosity flag is greater than 1
        self.notes_start_index = notes_start_index

        # Set the 'year' this file was made in
        year_regex = r'\d{4}'
        match = re.search(year_regex, self.filename)
        if match:
            self.year = int(match[0])

    def pprint(self, msg):
        self.stdout.write(self.style.SUCCESS(msg))

    def error_print(self, msg):
        self.stdout.write(self.style.ERROR(msg))

    def debug_print(self, msg):
        if self.is_debug_mode:
            self.pprint(msg)

    def debug_pprint(self, msg):
        self.debug_print(pprint.pformat(msg))

    def extract_note_and_number_from_line(self, line):
        '''
            Example line:
            [1] Briz M failure during second of three planned but...
            or
            (2) First SpaceX Falcon 1 attempt failed shortly...
        '''
        if line.startswith('('):
            split_character = ')'
        elif line.startswith('['):
            split_character = ']'
        line_parts = line.lstrip('[').lstrip('(').split(split_character)

        if(len(line_parts) == 2):
            return line_parts[0], line_parts[1]
        elif(len(line_parts) > 2): #cobble the line back together if there multiple split characers in the note for some reason
            return line_parts[0], split_character.join(line_parts[1:])
        elif(len(line_parts) == 1):
            return line_parts[0], '' #empty note I guess?
        else:
            raise ValueError(f"Note sure what to do with this line. Throwing a tantrum: {line}")

    def extract_note_from_continuation_line(self, line):
        return line

    def update_launch_with_note(self, note_number, note):
        launches = Launch.objects.filter(notes=note_number, launch_date__year=self.year)
        
        if(launches.count() <= 0):
            self.error_print(f"Could not find a launch for note: [{note_number}]: {note}")
            return
        
        for launch in launches:
            launch.notes = note
            launch.save()

    def parse(self):
        self.pprint(f"Parsing Launch Notes for {self.filename} starting at line {self.notes_start_index}")
        
        with open(self.filepath, 'r') as launch_stats_file:
            all_lines = launch_stats_file.readlines()

        launch_notes_lines = all_lines[self.notes_start_index:]

        current_note_number = -1
        is_continuation = False
        current_note = ''
        for note_line in launch_notes_lines:
            note_line = note_line.strip()
            self.debug_print(f"Current line: {note_line}")
            if '==============' in note_line:
                self.update_launch_with_note(current_note_number, current_note) #don't forget to update with the last note!
                break # reached the end of the notes

            if note_line.startswith('(') or note_line.startswith('['):
                if current_note_number != -1:
                    # we've reached a new note number, populate db with previous one's data
                    self.update_launch_with_note(current_note_number, current_note)

                current_note_number, current_note = self.extract_note_and_number_from_line(note_line)
                self.debug_print(f"Found a note: {current_note_number}, {current_note}")
            else:
                current_note += ' '
                current_note += self.extract_note_from_continuation_line(note_line)
                self.debug_print(f"Found a note continuation: {current_note}")
            

class LaunchStatsParser():
    def __init__(self, stdout, style, filepath, filename, is_debug_mode):
        self.stdout = stdout
        self.style = style
        self.filepath = filepath
        self.filename = filename
        self.file_should_be_modified = False #if we perform a line fix in the middle of parsing, we can now persist the fix
        self.is_debug_mode = is_debug_mode #Set to `True` when passed in --verbosity flag is greater than 1

        self.is_old_stats_style = ('2001' in filename) or ('2002' in filename)

    def pprint(self, msg):
        self.stdout.write(self.style.SUCCESS(msg))

    def debug_print(self, msg):
        if self.is_debug_mode:
            self.pprint(msg)

    def debug_pprint(self, msg):
        self.debug_print(pprint.pformat(msg))

    def get_launch_log_lines(self, lines):
        match_string = 'LAUNCH LOG' if self.is_old_stats_style else 'SPACE LAUNCH LOG'
        self.debug_print(f"Using match string: {match_string}")

        last_match_index = -1
        for index, line in enumerate(lines):
            if re.search(match_string, line, flags=re.IGNORECASE):
                last_match_index = index
        self.debug_print(f"Found match string at index: {last_match_index}")
        lines = lines[last_match_index:]
        data_start_match_string = '--------------------------------'
        data_start_raw_lines_index = last_match_index # used to track line numbers from the raw file
        for _, line in list(enumerate(lines)): #make a copy of the list in order to pop() without weird behavior
            lines.pop(0) #delete the line until we reach the match
            data_start_raw_lines_index += 1
            if data_start_match_string in line:
                break #we've already popped the current (and matching) line so the _next_ line should be the first data entry we're actually after
        
        data_end_match_string = '--------------------------------'
        data_end_match_index = -1
        # delete everything after the last data entry
        for index, line in enumerate(lines):
            if data_end_match_string in line:
                data_end_match_index = index
                break; #stop at the first match
        
        self.data_end_raw_lines_index = data_start_raw_lines_index + data_end_match_index
        result_lines = lines[:data_end_match_index]
        result_lines = [line.rstrip() for line in result_lines] #just trim off those pesky spaces at the end of a line

        self.pprint(f"Found {len(result_lines)} launch log entries! RAW LINE NUMBER START: {data_start_raw_lines_index}, END: {self.data_end_raw_lines_index}")

        result = dict(zip(range(data_start_raw_lines_index, self.data_end_raw_lines_index), result_lines))
        return result

    def get_data_end_match_index(self):
        return self.data_end_raw_lines_index

    def parse_launch_log_line_into_entry(self, line, index):
        replace_regex = r'[\s]{2,}' # regex for finding spots using more than one 'space'
        replace_symbol = '||' # replace them with this character (makes `split()` easier)
        subbed_line = re.sub(replace_regex, replace_symbol, line) # do the actual replacement
        entry = subbed_line.split(replace_symbol) # split on the replacement character

        # Error correction
        should_line_be_fixed = False
        while len(entry) < 7:
            should_line_be_fixed = True
            pyperclip.copy(line.strip('\n'))
            user_input = input(f"Bad parse for line [{index}]:\n{line}\nPlease provide fixed version.   'i' for UNKNOWN ID, 'm' for UNKNOWN MASS, 'o' (or any other key) for OTHER:\n")
            if user_input == 'i':
                entry.insert(2, "UNKNOWN") # "-1" means unknown mass
                fixed_line = '  '.join(entry).strip('\n') # allows us to reparse the string and save to file
            elif user_input == 'm':
                entry.insert(4, "-1") # "-1" means unknown mass
                fixed_line = '  '.join(entry).strip('\n') # allows us to reparse the string and save to file
            else:
                fixed_line = input("use ctrl+v to paste line from clipboard:\n")

            entry, _ = self.parse_launch_log_line_into_entry(fixed_line, index) #recursive call!

        if should_line_be_fixed: # do it here so we don't write the fix until it's fully correct
            self.update_file_with_fixed_launch_log_line(fixed_line, index)
                
        return entry, should_line_be_fixed

    def parse_date_from_raw_date(self, raw_date):
        '''
        Date format is probably one of:
        mm/dd/yy # e.g. 01/01/21, 03/01/21, 11/29/21 where year = 2021
        MMM d[d] # e.g Jan 1, Mar 17, Nov 29 etc
        mm/dd # 01/01, 03/17, 11/29
        '''
        date_match_strings = [
            '%b %d', # MMM d[d]
            '%m/%d/%y',
            '%m/%d'
        ]

        launch_date_time = None

        for date_match_string in date_match_strings:
            try:
                launch_date_time = datetime.strptime(raw_date, date_match_string)
            except ValueError:
                continue

        launch_date = launch_date_time.replace(year=self.CURRENT_YEAR).date()
        self.debug_print(f"Found launch date: {launch_date}")
        return launch_date

    def parse_launch_site_name_and_code_from_raw(self, raw_site):
        if ' ' in raw_site:
            tokens = raw_site.split()
        else:
            tokens = raw_site.split('/')
        name = tokens.pop(0)
        code = ' '.join(tokens)
        return name, code

    def parse_launch_orbit_name_and_notes_from_raw(self, raw_orbit):
        raw_orbit = raw_orbit.strip('*').strip('#').strip('&')
        if raw_orbit.startswith('['):
            # if the raw is something like [GEO] [3] then strip the first set of '[' and ']'
            raw_orbit = raw_orbit[1:raw_orbit.index(']')] + raw_orbit[raw_orbit.index(']')+1:]

        if raw_orbit.startswith('('):
            # if the raw is something like (GEO) (3) then strip the first set of '(' and ')'
            raw_orbit = raw_orbit[1:raw_orbit.index(')')] + raw_orbit[raw_orbit.index(')')+1:]

        if raw_orbit == '' or raw_orbit is None:
            raw_orbit = 'UNKNOWN'

        raw_orbit = raw_orbit.strip('\n').strip(' ')

        if '[' in raw_orbit:
            tokens = raw_orbit.strip(']').split('[')
        elif '(' in raw_orbit:
            tokens = raw_orbit.strip(')').split('(')
        else:
            tokens = [raw_orbit]
        code = tokens.pop(0).strip()
        is_uncertain = '?' in code
        code = code.strip('?')
        notes = '|'.join(tokens)
        return code, notes, is_uncertain

    def parse_launch_mass_from_raw(self, raw_mass):
        mass_scalar = raw_mass.strip('~').strip('?').strip('+')
        if self.CURRENT_YEAR == 2003:
            mass = float(mass_scalar)/1000
        else:
            mass = float(mass_scalar)
        return mass

    def create_launch_in_db(self, launch):
        vehicle_model, created = Vehicle.objects.get_or_create(name=launch['vehicle_name'])
        site_model, created = Site.objects.get_or_create(code=launch['site_name_code'])
        orbit_model, created = Orbit.objects.get_or_create(code__iexact=launch['orbit']['code'], defaults={'code': launch['orbit']['code']})
        
        launch_note_number = launch['orbit']['notes'] #temporarily store the note [number] left at the end of the line so a secondary parser can populate it. See: LaunchNotesParser
        
        launch_model, created = Launch.objects.get_or_create(
            launch_date=launch['date'],
            vehicle=vehicle_model,
            launch_id=launch['id'],
            payload=launch['payload'],
            mass=launch['mass'],
            site=site_model,
            site_pad_code=launch['site_pad_code'],
            orbit=orbit_model,
            orbit_uncertain=launch['orbit']['uncertain']
        )

        launch_model.notes = launch_note_number
        launch_model.save()

    def update_file_with_fixed_launch_log_line(self, fixed_line, index):
        with open(self.filepath, 'r') as statsfile:
            lines = statsfile.readlines()

        lines[index] = fixed_line + "\n"

        with open(self.filepath, 'w') as statsfile:
            statsfile.writelines(lines)


    def populate_db_from_launch_log(self, lines):
        # self.debug_print(pprint.pformat(lines))
        for index, line in lines.items():
            if line.strip() == '':
                continue
            entry, had_manual_correction = self.parse_launch_log_line_into_entry(line, index)
            self.debug_pprint(entry)
            launch_date = self.parse_date_from_raw_date(entry[0])
            site_name_code, site_pad_code = self.parse_launch_site_name_and_code_from_raw(entry[5])
            orbit_code, orbit_notes, is_uncertain = self.parse_launch_orbit_name_and_notes_from_raw(entry[-1])
            mass = self.parse_launch_mass_from_raw(entry[4])

            launch = {
                "date": launch_date,
                "vehicle_name": entry[1],
                "id": entry[2],
                "payload": entry[3],
                "mass": mass, 
                "site_pad_code": site_pad_code,
                "site_name_code": site_name_code,
                "orbit": {"code": orbit_code, "notes": orbit_notes, "uncertain": is_uncertain}, 
            }

            if had_manual_correction: # nice to see the fixed structure when you're making those edits...
                self.pprint(pprint.pformat(launch))
            else:
                self.debug_pprint(launch)

            self.create_launch_in_db(launch)

    def has_launch_notes(self):
        years_without_notes = ['2001', '2002', '2003']
        for year in years_without_notes:
            if year in self.filename:
                return False
        return True

    def parse(self):
        with open(self.filepath) as statsfile:
            self.debug_print(f"reading file: {statsfile}")
            statsfile_lines = statsfile.readlines()

        # Set the 'year' this file was made in
        year_regex = r'\d{4}'
        match = re.search(year_regex, self.filename)
        if match:
            self.CURRENT_YEAR = int(match[0])

        self.debug_print("Parsing file...")
        launch_log_lines = self.get_launch_log_lines(statsfile_lines)
        self.debug_print("Populating DB with launch log entries...")
        self.populate_db_from_launch_log(launch_log_lines)

        if self.has_launch_notes():
            launch_data_end_index = self.get_data_end_match_index()
            notes_parser = LaunchNotesParser(self.stdout, self.style, self.filepath, self.filename, self.is_debug_mode, launch_data_end_index + 1)
            notes_parser.parse()



class Command(BaseCommand):
    help = 'Parses the LAUNCH STATS txt data files located in the initial_data/ folder'
    IS_DEBUG_MODE = False #Set to `True` when passed in --verbosity flag is greater than 1

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', '-f',
            action='store',
            dest="statsfile",
            help='Specify a specific file instead of parsing all the files in the spacetrends/initial_data/ folder.',
        )

    def pprint(self, msg):
        self.stdout.write(self.style.SUCCESS(msg))

    def debug_print(self, msg):
        if self.IS_DEBUG_MODE:
            self.pprint(msg)

    def debug_pprint(self, msg):
        self.debug_print(pprint.pformat(msg))

    def is_launch_stats_file(self, filename):
        ''' Checks if this file is a regular 'launch stats' file '''
        year_regex = r'\d{4}'
        match = re.search(year_regex, filename)
        return bool(match)

    def is_site_codes_file(self, filename):
        return "SITE_CODES" in filename

    def is_orbit_codes_file(self, filename):
        return "ORBIT_CODES" in filename

    def set_verbosity(self, options):
        if options['verbosity'] > 1:
            self.pprint(f"Verbosity set to {options['verbosity']}. Enabling DEBUG output.")
            self.IS_DEBUG_MODE = True

    def parse_file(self, filepath, filename):
        self.pprint(f"File name: {filename}, File path: {filepath}")
        
        if self.is_launch_stats_file(filename):
            self.debug_print(f"Parsing LAUNCH STATS file: {filename}")
            parser = LaunchStatsParser(self.stdout, self.style, filepath, filename, self.IS_DEBUG_MODE)
        elif self.is_site_codes_file(filename):
            self.debug_print(f"Parsing SITE_CODES file: {filename}")
            parser = SiteCodesParser(self.stdout, self.style, filepath, filename, self.IS_DEBUG_MODE)
        elif self.is_orbit_codes_file(filename):
            self.debug_print(f"Parsing ORBIT_CODES file: {filename}")
            parser = OrbitCodesParser(self.stdout, self.style, filepath, filename, self.IS_DEBUG_MODE)
        else:
            self.pprint(f"NOT SURE WHAT TO DO WITH THIS FILE: {filename}")
            return False

        parser.parse()

    def handle(self, *args, **options):
        self.set_verbosity(options)

        self.debug_print(options)

        if options['statsfile']:
            path = Path(options['statsfile'])
            self.parse_file(str(path), path.name)
        else:
            with scandir('spacetrends/initial_data') as entries:
                for entry in entries:
                    if not entry.is_file():
                        continue
                    self.parse_file(entry.path, entry.name)
