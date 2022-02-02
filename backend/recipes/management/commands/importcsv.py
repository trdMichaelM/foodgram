"""
Examples: python manage.py importcsv --path "/home/michael/dev/foodgram-project-react/data/ingredients.csv" --model_name "recipes.Ingredient"
          python manage.py importcsv --path "data/ingredients.csv" --model_name "recipes.Ingredient"
          python manage.py importcsv --path "data/tags.csv" --model_name "recipes.Tag"
"""
import csv

from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.db.utils import IntegrityError


class Command(BaseCommand):
    help = 'Import data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help="file path")
        parser.add_argument('--model_name', type=str, help="model name")

    def handle(self, *args, **options):
        file_path = options['path']

        try:
            model = apps.get_model(options['model_name'])
        except Exception as err:
            raise CommandError(str(err))

        try:
            file = open(file_path, 'r')
        except IOError as err:
            raise CommandError(str(err))

        reader = csv.reader(file, delimiter=',')
        header = reader.__next__()
        for row in reader:
            data = {key: value for key, value in zip(header, row)}
            try:
                model.objects.create(**data)
            except IntegrityError as err:
                line = ', '.join(row)
                raise CommandError(f'{err}, \"{line}\"')
            except Exception as err:
                raise CommandError(str(err))

        file.close()
