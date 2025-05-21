from django.core.management.base import BaseCommand
from django.urls import get_resolver, URLPattern, URLResolver
from rest_framework.schemas.openapi import SchemaGenerator
from drf_spectacular.generators import SchemaGenerator as SpectacularSchemaGenerator
from importlib import import_module

class Command(BaseCommand):
    help = 'Generates API schema using drf-spectacular without requiring a request'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Path to output the schema file')
        parser.add_argument('--format', type=str, default='json', choices=['json', 'yaml'], help='Schema format')

    def handle(self, *args, **options):
        output_file = options.get('file')
        output_format = options.get('format')

        # Create a SchemaGenerator using drf-spectacular
        spectacular_generator = SpectacularSchemaGenerator()
        schema = spectacular_generator.get_schema(request=None, public=True)

        # Output schema
        if output_file:
            if output_format == 'yaml':
                import yaml
                with open(output_file, 'w') as outfile:
                    yaml.dump(schema, outfile, default_flow_style=False)
            else:
                import json
                with open(output_file, 'w') as outfile:
                    json.dump(schema, outfile, indent=2)
            self.stdout.write(self.style.SUCCESS(f'Schema written to {output_file}'))
        else:
            import json
            self.stdout.write(json.dumps(schema, indent=2))
