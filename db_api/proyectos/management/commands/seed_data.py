import json
import os
from django.core.management.base import BaseCommand
from proyectos.models import Project, Property, Typology
from django.conf import settings


class Command(BaseCommand):
    help = 'Seed database with projects, properties and typologies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Property.objects.all().delete()
            Project.objects.all().delete()
            Typology.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Data cleared!'))

        # Get the base directory
        base_dir = settings.BASE_DIR
        seed_data_dir = os.path.join(base_dir, 'seed_data')

        # Load typologies
        self.stdout.write(self.style.MIGRATE_HEADING('Loading typologies...'))
        typologies_file = os.path.join(seed_data_dir, 'typologies.json')

        with open(typologies_file, 'r', encoding='utf-8') as f:
            typologies_data = json.load(f)

        typologies_map = {}
        for typo_data in typologies_data['typologies']:
            typology = Typology.objects.create(
                name=typo_data['name'],
                description=typo_data.get('description'),
                type=typo_data.get('type'),
                num_bedrooms=typo_data['num_bedrooms'],
                num_bathrooms=typo_data['num_bathrooms'],
                area_m2=typo_data['area_m2']
            )
            typologies_map[typo_data['name']] = typology

        self.stdout.write(self.style.SUCCESS(f'Created {len(typologies_map)} typologies'))

        # Load projects and properties
        self.stdout.write(self.style.MIGRATE_HEADING('Loading projects and properties...'))
        projects_file = os.path.join(seed_data_dir, 'projects_properties.json')

        with open(projects_file, 'r', encoding='utf-8') as f:
            projects_data = json.load(f)

        projects_count = 0
        properties_count = 0

        for project_data in projects_data['projects']:
            # Create project
            project = Project.objects.create(
                name=project_data['name'],
                description=project_data['description'],
                district=project_data['district'],
                address=project_data['address'],
                reference=project_data['reference'],
                details=project_data['details'],
                video_url=project_data.get('video_url'),
                brochure_url=project_data.get('brochure_url'),
                includes_parking=project_data.get('includes_parking', False),
                has_showroom=project_data.get('has_showroom', False)
            )
            projects_count += 1

            # Create properties for this project
            for prop_data in project_data.get('properties', []):
                # Assign a random typology based on property characteristics
                # For now, we'll assign typologies based on naming patterns
                typology = self._find_suitable_typology(prop_data, typologies_map)

                Property.objects.create(
                    title=prop_data['title'],
                    type=prop_data['type'],
                    description=prop_data['description'],
                    pricing=prop_data['pricing'],
                    view_type=prop_data['view_type'],
                    floor_no=prop_data['floor_no'],
                    project_id=project,
                    typology_id=typology
                )
                properties_count += 1

        self.stdout.write(self.style.SUCCESS(f'Created {projects_count} projects'))
        self.stdout.write(self.style.SUCCESS(f'Created {properties_count} properties'))
        self.stdout.write(self.style.SUCCESS('✅ Data seeding completed!'))

    def _find_suitable_typology(self, prop_data, typologies_map):
        """Find a suitable typology based on property data"""
        prop_type = prop_data.get('type', '').lower()

        # Simple mapping logic - you can enhance this
        if 'penthouse' in prop_data['title'].lower():
            # Find a penthouse typology
            for name, typo in typologies_map.items():
                if 'Penthouse' in name:
                    return typo

        elif 'loft' in prop_data['title'].lower() or 'loft' in prop_type:
            for name, typo in typologies_map.items():
                if 'Loft' in name:
                    return typo

        elif 'studio' in prop_data['title'].lower() or 'studio' in prop_type:
            for name, typo in typologies_map.items():
                if 'Studio' in name:
                    return typo

        elif 'oficina' in prop_type:
            for name, typo in typologies_map.items():
                if 'Oficina' in name:
                    return typo

        elif 'local' in prop_type:
            for name, typo in typologies_map.items():
                if 'Local' in name:
                    return typo

        elif 'terreno' in prop_type:
            for name, typo in typologies_map.items():
                if 'Terreno' in name:
                    return typo

        elif 'casa_playa' in prop_type:
            for name, typo in typologies_map.items():
                if 'Casa Playa' in name:
                    return typo

        elif 'casa_campo' in prop_type:
            for name, typo in typologies_map.items():
                if 'Casa Campestre' in name:
                    return typo

        elif 'casa' in prop_type:
            for name, typo in typologies_map.items():
                if 'Casa' in name and 'Playa' not in name and 'Campestre' not in name and 'Adosada' not in name:
                    return typo

        elif 'duplex' in prop_data['title'].lower() or 'dúplex' in prop_data['title'].lower():
            for name, typo in typologies_map.items():
                if 'Dúplex' in name or 'Duplex' in name:
                    return typo

        # Default to departamento typologies
        for name, typo in typologies_map.items():
            if 'Departamento' in name:
                return typo

        # Fallback to first typology
        return list(typologies_map.values())[0]
