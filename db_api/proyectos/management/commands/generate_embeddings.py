import json
import time
import boto3
from django.core.management.base import BaseCommand
from proyectos.models import Project, Property
from dotenv import load_dotenv
import os

load_dotenv()


class Command(BaseCommand):
    help = 'Generate embeddings for Projects and Properties using AWS Bedrock'

    def __init__(self):
        super().__init__()
        self.AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
        self.AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.MODEL_ID = "amazon.nova-2-multimodal-embeddings-v1:0"
        self.EMBEDDING_DIMENSION = 3072

        # Initialize Amazon Bedrock Runtime client
        self.bedrock_runtime = boto3.client(
            "bedrock-runtime",
            region_name="us-east-1",
            aws_access_key_id=self.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY
        )

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            default='projects',
            choices=['projects', 'properties', 'all'],
            help='Which model to generate embeddings for (projects, properties, or all)',
        )

    def handle(self, *args, **options):
        model_choice = options['model']

        if model_choice in ['projects', 'all']:
            self.generate_project_embeddings()

        if model_choice in ['properties', 'all']:
            self.generate_property_embeddings()

        self.stdout.write(self.style.SUCCESS('✅ Embedding generation completed!'))

    def generate_embedding(self, text):
        """Generate embedding for given text using AWS Bedrock"""
        try:
            request_body = {
                "taskType": "SINGLE_EMBEDDING",
                "singleEmbeddingParams": {
                    "embeddingPurpose": "GENERIC_INDEX",
                    "embeddingDimension": self.EMBEDDING_DIMENSION,
                    "text": {"truncationMode": "END", "value": text},
                },
            }

            response = self.bedrock_runtime.invoke_model(
                body=json.dumps(request_body),
                modelId=self.MODEL_ID,
                contentType="application/json",
            )

            response_body = json.loads(response["body"].read())
            embedding = response_body["embeddings"][0]["embedding"]

            return embedding

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating embedding: {str(e)}'))
            return None

    def generate_project_embeddings(self):
        """Generate embeddings for all Projects"""
        self.stdout.write(self.style.MIGRATE_HEADING('Generating embeddings for Projects...'))

        projects = Project.objects.all()
        total = projects.count()

        for idx, project in enumerate(projects, 1):
            # Combine fields for embedding: name + description + details + district
            text_parts = []

            if project.name:
                text_parts.append(project.name)
            if project.description:
                text_parts.append(project.description)
            if project.details:
                text_parts.append(project.details)
            if project.district:
                text_parts.append(f"Ubicado en {project.district}")

            combined_text = " ".join(text_parts)

            if not combined_text.strip():
                self.stdout.write(self.style.WARNING(f'Skipping project {project.id} - no text to embed'))
                continue

            # Generate embedding
            self.stdout.write(f'Processing project {idx}/{total}: {project.name}')
            embedding = self.generate_embedding(combined_text)

            if embedding:
                # Save embedding to database
                project.busqueda = embedding
                project.save(update_fields=['busqueda'])
                self.stdout.write(self.style.SUCCESS(f'✓ Saved embedding for {project.name}'))

            # Rate limiting - pequeña pausa entre requests
            time.sleep(0.5)

        self.stdout.write(self.style.SUCCESS(f'Completed {total} projects'))

    def generate_property_embeddings(self):
        """Generate embeddings for all Properties"""
        self.stdout.write(self.style.MIGRATE_HEADING('Generating embeddings for Properties...'))

        properties = Property.objects.all()
        total = properties.count()

        for idx, prop in enumerate(properties, 1):
            # Combine fields for embedding: title + description + view_type
            text_parts = []

            if prop.title:
                text_parts.append(prop.title)
            if prop.description:
                text_parts.append(prop.description)
            if prop.view_type:
                text_parts.append(f"Vista: {prop.view_type}")

            combined_text = " ".join(text_parts)

            if not combined_text.strip():
                self.stdout.write(self.style.WARNING(f'Skipping property {prop.id} - no text to embed'))
                continue

            # Generate embedding
            self.stdout.write(f'Processing property {idx}/{total}: {prop.title}')
            embedding = self.generate_embedding(combined_text)

            if embedding:
                # Save embedding to database
                prop.busqueda = embedding
                prop.save(update_fields=['busqueda'])
                self.stdout.write(self.style.SUCCESS(f'✓ Saved embedding for {prop.title}'))

            # Rate limiting - pequeña pausa entre requests
            time.sleep(0.5)

        self.stdout.write(self.style.SUCCESS(f'Completed {total} properties'))
