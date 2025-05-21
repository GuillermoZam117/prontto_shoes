#!/usr/bin/env python
"""
Script to generate API schema directly using drf-spectacular
"""
import os
import sys
import django
from pathlib import Path

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.renderers import OpenApiJsonRenderer, OpenApiYamlRenderer

def generate_schema(output_path=None, format='json'):
    """Generate OpenAPI schema using drf-spectacular"""
    print("Generating API schema...")
    
    # Create schema generator
    generator = SchemaGenerator()
    
    try:
        # Generate schema
        schema = generator.get_schema(request=None, public=True)
        
        # Select renderer based on format
        if format.lower() == 'yaml':
            renderer = OpenApiYamlRenderer()
        else:
            renderer = OpenApiJsonRenderer()
        
        # Render schema
        content = renderer.render(schema)
        
        # Write to file or stdout
        if output_path:
            with open(output_path, 'wb') as file_obj:
                file_obj.write(content)
            print(f"Schema written to {output_path}")
        else:
            sys.stdout.buffer.write(content)
            
        return True
    except Exception as e:
        print(f"Error generating schema: {e}")
        return False

if __name__ == "__main__":
    # Parse command-line arguments
    output_path = None
    output_format = 'json'
    
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_format = sys.argv[2]
    
    # Generate schema
    success = generate_schema(output_path, output_format)
    sys.exit(0 if success else 1)
