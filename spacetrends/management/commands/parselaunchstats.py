from os import scandir
import re

from django.core.management.base import BaseCommand, CommandError

from spacetrends.models import Vehicle




class Command(BaseCommand):
    help = 'Parses the LAUNCH STATS txt data files located in the initial_data/ folder'

    IS_OLD_STATS_STYLE = False

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

    def get_launch_log_lines(self, lines):
        match_string = 'LAUNCH LOG' if self.IS_OLD_STATS_STYLE else 'SPACE LAUNCH LOG'
        self.pprint(f"Using match string: {match_string}")
        last_match_index = -1
        for index, line in enumerate(lines):
            if re.search(match_string, line, flags=re.IGNORECASE):
                last_match_index = index
        self.pprint(f"Found match string at index: {last_match_index}")
        lines = lines[last_match_index:]
        data_start_match_string = '--------------------------------'
        for _, line in list(enumerate(lines)): #make a copy of the list in order to pop() without weird behavior
            lines.pop(0) #delete the line until we reach the match
            if data_start_match_string in line:
                break #we've already popped the current (and matching) line so the _next_ line should be the first data entry we're actually after
        
        data_end_match_string = '--------------------------------'
        data_end_match_index = -1
        # delete everything after the last data entry
        for index, line in enumerate(lines):
            if data_end_match_string in line:
                data_end_match_index = index
                break; #stop at the first match
        
        result = lines[:data_end_match_index]
        self.pprint(f"Found {len(result)} launch log entries!")
        # for entry in result:
        #     self.pprint(f"ENTRY: {entry}")
        # self.pprint(result)
        return result

    def populate_db_from_launch_log(self, lines):
        pass

    def parse_stats_file(self, statsfilepath):
        with open(statsfilepath) as statsfile:
            self.pprint(f"reading file: {statsfile}")
            statsfile_lines = statsfile.readlines()

        self.pprint("Parsing file...")
        launch_log_lines = self.get_launch_log_lines(statsfile_lines)
        self.pprint("Populating DB with launch log entries...")
        self.populate_db_from_launch_log(launch_log_lines)


    def handle(self, *args, **options):
        self.pprint(options)
        if options['statsfile']:
            filename = options['statsfile']
            if ('2001' in filename) or ('2002' in filename):
                self.pprint(f"Using old stats style parsing for {filename}")
                self.IS_OLD_STATS_STYLE = True
            else:
                self.IS_OLD_STATS_STYLE = False
            self.parse_stats_file(options['statsfile'])
        else:
            with scandir('spacetrends/initial_data') as entries:
                for entry in entries:
                    if(entry.is_file()):
                        self.pprint(f"ENTRY NAME: {entry.name}")
                        if ('2001' in entry.name) or ('2002' in entry.name):
                            self.pprint(f"Using old stats style parsing for {entry.name}")
                            self.IS_OLD_STATS_STYLE = True
                        else:
                            self.IS_OLD_STATS_STYLE = False
                        self.parse_stats_file(entry.path)


        # for poll_id in options['poll_ids']:
        #     try:
        #         poll = Poll.objects.get(pk=poll_id)
        #     except Poll.DoesNotExist:
        #         raise CommandError('Poll "%s" does not exist' % poll_id)

        #     poll.opened = False
        #     poll.save()

        #     self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))