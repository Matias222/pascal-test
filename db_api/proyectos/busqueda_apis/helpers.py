import json
import aioboto3
import os
import hashlib
from django.core.cache import cache

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
MODEL_ID = "amazon.nova-2-multimodal-embeddings-v1:0"
EMBEDDING_DIMENSION = 3072

#Importante usar async para la query!

async def generate_query_embedding_async(text:str):

    """Generate embedding for search query using AWS Bedrock (async with cache)"""

    # Check cache first - use hash to avoid special characters
    text_normalized = text.lower().strip()
    text_hash = hashlib.md5(text_normalized.encode('utf-8')).hexdigest()
    cache_key = f"emb_{text_hash}"
    cached_embedding = cache.get(cache_key)

    if cached_embedding:
        return cached_embedding

    try:
        # Create async boto3 session
        session = aioboto3.Session()

        async with session.client(
            "bedrock-runtime",
            region_name="us-east-1",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        ) as bedrock_runtime:

            request_body = {
                "taskType": "SINGLE_EMBEDDING",
                "singleEmbeddingParams": {
                    "embeddingPurpose": "GENERIC_INDEX",
                    "embeddingDimension": EMBEDDING_DIMENSION,
                    "text": {"truncationMode": "END", "value": text},
                },
            }

            response = await bedrock_runtime.invoke_model(
                body=json.dumps(request_body),
                modelId=MODEL_ID,
                contentType="application/json",
            )

            response_body = json.loads(await response["body"].read())
            embedding = response_body["embeddings"][0]["embedding"]

            cache.set(cache_key, embedding, 60*60*24) #24 horas

            return embedding

    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return None
