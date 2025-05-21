from django.core.management.base import BaseCommand, CommandError
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.renderers import OpenApiJsonRenderer, OpenApiYamlRenderer

class Command(BaseCommand):
    help = "Generate an OpenAPI schema for your API using drf-spectacular."

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', 
            type=str, 
            help='Output file for schema (defaults to stdout)'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'yaml'],
            default='json',
            help='Output format for schema'
        )

    def handle(self, *args, **options):
        output_file = options['file']
        output_format = options['format']
        
        # Generate schema using drf-spectacular directly
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)
        
        # Select renderer based on format
        if output_format == 'yaml':
            renderer = OpenApiYamlRenderer()
        else:
            renderer = OpenApiJsonRenderer()
        
        # Render schema
        content = renderer.render(schema)
        
        # Write to file or stdout
        if output_file:
            with open(output_file, 'wb') as file_obj:
                file_obj.write(content)
            self.stdout.write(self.style.SUCCESS(f"Schema written to {output_file}"))
        else:
            self.stdout.write(content.decode('utf-8'))
