from datetime import datetime
import pprint
import re
from os import scandir

from django.core.management.base import BaseCommand, CommandError

import pyperclip

from spacetrends.models import Launch, Orbit, Site, Vehicle

class launch_stats_parser():
    def __init__(self, stdout, style, filepath, filename, is_debug_mode, is_old_stats_style):
        self.stdout = stdout
        self.style = style
        self.filepath = filepath
        self.filename = filename
        self.year = 0000
        self.file_should_be_modified = False #if we perform a line fix in the middle of parsing, we can now persist the fix
        self.is_debug_mode = is_debug_mode #Set to `True` when passed in --verbosity flag is greater than 1
        self.is_old_stats_style = is_old_stats_style

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
        
        data_end_raw_lines_index = data_start_raw_lines_index + data_end_match_index
        result_lines = lines[:data_end_match_index]

        self.pprint(f"Found {len(result_lines)} launch log entries! RAW LINE NUMBER START: {data_start_raw_lines_index}, END: {data_end_raw_lines_index}")

        result = dict(zip(range(data_start_raw_lines_index, data_end_raw_lines_index), result_lines))
        return result

    def parse_launch_log_line_into_list_symbols(self, line):
        replace_regex = r'[\s]{2,}' # regex for finding spots using more than one 'space'
        replace_symbol = '||' # replace them with this character (makes `split()` easier)
        subbed_line = re.sub(replace_regex, replace_symbol, line) # do the actual replacement
        entry = subbed_line.split(replace_symbol) # split on the replacement character
        return entry

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

    def parse_launch_orbit_name_and_code_from_raw(self, raw_orbit):
        raw_orbit = raw_orbit.strip('*').strip('#').strip('&')
        if raw_orbit.startswith('['):
            # if the raw is something like [GEO] [3] then strip the first set of '[' and ']'
            raw_orbit = raw_orbit[1:raw_orbit.index(']')] + raw_orbit[raw_orbit.index(']')+1:]

        if raw_orbit.startswith('('):
            # if the raw is something like [GEO] [3] then strip the first set of '[' and ']'
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
        code = tokens.pop(0)
        notes = '|'.join(tokens)
        return code, notes

    def parse_launch_mass_from_raw(self, raw_mass):
        return raw_mass.strip('~').strip('?').strip('+')

    def create_launch_in_db(self, launch):
        vehicle_model, created = Vehicle.objects.get_or_create(name=launch['vehicle_name'])
        site_model, created = Site.objects.get_or_create(code=launch['site_name_code'])
        orbit_model, created = Orbit.objects.get_or_create(code=launch['orbit']['code'])
        launch_model, created = Launch.objects.get_or_create(
            launch_date=launch['date'],
            vehicle=vehicle_model,
            launch_id=launch['id'],
            payload=launch['payload'],
            mass=launch['mass'],
            site=site_model,
            site_pad_code=launch['site_pad_code'],
            orbit=orbit_model
        )

    def update_file_with_fixed_launch_log_line(self, fixed_line, index):
        with open(self.filepath, 'r') as statsfile:
            lines = statsfile.readlines()

        lines[index] = fixed_line + "\n"

        with open(self.filepath, 'w') as statsfile:
            statsfile.writelines(lines)


    def populate_db_from_launch_log(self, lines):
        # self.debug_print(pprint.pformat(lines))
        for index, line in lines.items():
            entry = self.parse_launch_log_line_into_list_symbols(line)
            should_line_be_fixed = False
            while len(entry) < 7:
                should_line_be_fixed = True
                pyperclip.copy(line.strip('\n'))
                fixed_line = input(f"Bad parse for line [{index}]:\n{line}\nPlease provide fixed version (use ctrl+v to paste line from clipboard):\n")
                entry = self.parse_launch_log_line_into_list_symbols(fixed_line)

            if should_line_be_fixed: # do it here so we don't write the fix until it's fully correct
                self.update_file_with_fixed_launch_log_line(fixed_line, index)
                
            self.debug_pprint(entry)
            launch_date = self.parse_date_from_raw_date(entry[0])
            site_name_code, site_pad_code = self.parse_launch_site_name_and_code_from_raw(entry[5])
            orbit_code, orbit_notes = self.parse_launch_orbit_name_and_code_from_raw(entry[6])
            mass = self.parse_launch_mass_from_raw(entry[4])

            launch = {
                "date": launch_date,
                "vehicle_name": entry[1],
                "id": entry[2],
                "payload": entry[3],
                "mass": mass, 
                "site_pad_code": site_pad_code,
                "site_name_code": site_name_code,
                "orbit": {"code": orbit_code, "notes": orbit_notes} 
            }

            if should_line_be_fixed: # nice to see the fixed structure when you're making those edits...
                self.pprint(pprint.pformat(launch))
            else:
                self.debug_pprint(launch)

            self.create_launch_in_db(launch)



    def parse_stats_file(self):
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



class Command(BaseCommand):
    help = 'Parses the LAUNCH STATS txt data files located in the initial_data/ folder'
    IS_DEBUG_MODE = False #Set to `True` when passed in --verbosity flag is greater than 1

    def add_arguments(self, parser):
        # #positional arg
        # parser.add_argument('poll_ids', nargs='+', type=int)
        # Named (optional) arguments
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

    def handle(self, *args, **options):
        if options['verbosity'] > 1:
            self.pprint(f"Verbosity set to {options['verbosity']}. Enabling DEBUG output.")
            self.IS_DEBUG_MODE = True

        self.debug_print(options)
        if options['statsfile']:
            filename = options['statsfile']
            if ('2001' in filename) or ('2002' in filename):
                self.debug_print(f"Using old stats style parsing for {filename}")
                is_old_stats_style = True
            else:
                is_old_stats_style = False

        #     def __init__(self, stdout, filepath, filename, is_debug_mode, is_old_stats_style):

            parser = launch_stats_parser(self.stdout, self.style, options['statsfile'], filename, self.IS_DEBUG_MODE, is_old_stats_style)
            parser.parse_stats_file()
        else:
            with scandir('spacetrends/initial_data') as entries:
                for entry in entries:
                    if(entry.is_file()):
                        self.pprint(f"File name: {entry.name}")
                        if ('2001' in entry.name) or ('2002' in entry.name):
                            self.debug_print(f"Using old stats style parsing for {entry.name}")
                            is_old_stats_style = True
                        else:
                            is_old_stats_style = False
                        parser = launch_stats_parser(self.stdout, self.style, entry.path, entry.name, self.IS_DEBUG_MODE, is_old_stats_style)
                        parser.parse_stats_file()
