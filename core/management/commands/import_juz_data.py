import json
import os
from django.core.management.base import BaseCommand
from core.models import Juz, SurahPageData


class Command(BaseCommand):
    help = 'Import juz data from JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir',
            type=str,
            help='Directory containing juz JSON files (default: core/data/quran_juz_data)',
        )

    def handle(self, *args, **options):
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        default_dir = os.path.join(base_dir, 'data', 'quran_juz_data')
        data_dir = options.get('dir') or default_dir

        if not os.path.isdir(data_dir):
            self.stdout.write(self.style.ERROR(f'Directory not found: {data_dir}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Importing juz data from: {data_dir}'))

        juz_created = 0
        juz_updated = 0
        surah_created = 0
        surah_updated = 0

        for filename in os.listdir(data_dir):
            if filename.startswith('juz_') and filename.endswith('.json'):
                filepath = os.path.join(data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    juz_number = data['juz_number']

                    # Create or update Juz
                    juz_obj, juz_created_flag = Juz.objects.update_or_create(
                        juz_number=juz_number,
                        defaults={
                            'start_page': data['start_page'],
                            'end_page': data['end_page'],
                            'total_pages': data['total_pages'],
                            'is_active': True,
                        }
                    )
                    if juz_created_flag:
                        juz_created += 1
                    else:
                        juz_updated += 1

                    # Process surahs in this juz
                    for surah in data['surahs']:
                        surah_obj, surah_created_flag = SurahPageData.objects.update_or_create(
                            surah_number=surah['surah_number'],
                            juz=str(juz_number),
                            defaults={
                                'name': surah['surah_name'],
                                'surah_name_arabic': surah['surah_name_arabic'],
                                'juz_number': juz_number,
                                'start_page': surah['start_page'],
                                'end_page': surah['end_page'],
                                'start_page_decimal': surah['start_page_decimal'],
                                'end_page_decimal': surah['end_page_decimal'],
                                'pages': surah['end_page_decimal'] - surah['start_page_decimal'],
                                'is_active': True,
                            }
                        )
                        if surah_created_flag:
                            surah_created += 1
                        else:
                            surah_updated += 1

                    self.stdout.write(f'Successfully processed: {filename}')

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing {filename}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'Import complete!'))
        self.stdout.write(f'  Juz: Created {juz_created}, Updated {juz_updated}')
        self.stdout.write(f'  Surahs: Created {surah_created}, Updated {surah_updated}')
