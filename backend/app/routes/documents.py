"""Document processing routes"""
import os
import tempfile
import time
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas import StandardResponse

# Import processing modules
from src.document_processing.doc_processor import DocumentProcessor
from src.embeddings.embedding_generator import EmbeddingGenerator
from src.vector_database.qdrant_vector_db import QdrantVectorDB
from src.audio_processing.audio_transcriber import AudioTranscriber
from src.audio_processing.youtube_transcriber import YouTubeTranscriber
from src.web_scraping.web_scraper import WebScraper

router = APIRouter()

# Request models
class URLsRequest(BaseModel):
    urls: List[str]

class YouTubeRequest(BaseModel):
    url: str

class TextRequest(BaseModel):
    text: str
    title: Optional[str] = None

# Initialize pipeline components (singleton pattern)
_pipeline_components = {}

def get_pipeline_components():
    """Get or initialize pipeline components"""
    if not _pipeline_components:
        _pipeline_components['doc_processor'] = DocumentProcessor()
        _pipeline_components['embedding_generator'] = EmbeddingGenerator()
        _pipeline_components['vector_db'] = QdrantVectorDB()
        
        # Optional components - always initialize keys, set to None if not available
        if os.getenv('ASSEMBLYAI_API_KEY'):
            assemblyai_api_key = os.getenv('ASSEMBLYAI_API_KEY')
            _pipeline_components['audio_transcriber'] = AudioTranscriber(api_key=assemblyai_api_key)
            _pipeline_components['youtube_transcriber'] = YouTubeTranscriber(assemblyai_api_key=assemblyai_api_key)
        else:
            _pipeline_components['audio_transcriber'] = None
            _pipeline_components['youtube_transcriber'] = None
            
        if os.getenv('FIRECRAWL_API_KEY'):
            _pipeline_components['web_scraper'] = WebScraper(api_key=os.getenv('FIRECRAWL_API_KEY'))
        else:
            _pipeline_components['web_scraper'] = None
    else:
        # Ensure all keys exist even if components were initialized before
        if 'web_scraper' not in _pipeline_components:
            if os.getenv('FIRECRAWL_API_KEY'):
                _pipeline_components['web_scraper'] = WebScraper(api_key=os.getenv('FIRECRAWL_API_KEY'))
            else:
                _pipeline_components['web_scraper'] = None
        if 'audio_transcriber' not in _pipeline_components:
            if os.getenv('ASSEMBLYAI_API_KEY'):
                assemblyai_api_key = os.getenv('ASSEMBLYAI_API_KEY')
                _pipeline_components['audio_transcriber'] = AudioTranscriber(api_key=assemblyai_api_key)
                _pipeline_components['youtube_transcriber'] = YouTubeTranscriber(assemblyai_api_key=assemblyai_api_key)
            else:
                _pipeline_components['audio_transcriber'] = None
                _pipeline_components['youtube_transcriber'] = None
    
    return _pipeline_components

@router.post("/upload", response_model=StandardResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload and process files"""
    components = get_pipeline_components()
    processed_sources = []
    
    try:
        for uploaded_file in files:
            try:
                # Save uploaded file to temp location
                suffix = Path(uploaded_file.filename).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                    content = await uploaded_file.read()
                    tmp_file.write(content)
                    temp_path = tmp_file.name
                
                # Process based on file type
                if uploaded_file.content_type and uploaded_file.content_type.startswith('audio/'):
                    if not components['audio_transcriber']:
                        raise HTTPException(
                            status_code=400,
                            detail="Audio processing not available (missing ASSEMBLYAI_API_KEY)"
                        )
                    chunks = components['audio_transcriber'].transcribe_audio(temp_path)
                    source_type = "Audio"
                    for chunk in chunks:
                        chunk.source_file = uploaded_file.filename
                else:
                    chunks = components['doc_processor'].process_document(temp_path)
                    source_type = "Document"
                    for chunk in chunks:
                        chunk.source_file = uploaded_file.filename
                
                if chunks:
                    # Generate embeddings and store
                    embedded_chunks = components['embedding_generator'].generate_embeddings(chunks)
                    
                    # Create index if first document
                    if len(processed_sources) == 0:
                        components['vector_db'].create_index(use_binary_quantization=False)
                    
                    # Insert embeddings with user_id for user-specific isolation
                    user_id = str(current_user.id)
                    components['vector_db'].insert_embeddings(embedded_chunks, user_id=user_id)
                    
                    source_info = {
                        'name': uploaded_file.filename,
                        'type': source_type,
                        'size': f"{len(content) / 1024:.1f} KB",
                        'chunks': len(chunks),
                        'uploaded_at': time.strftime("%Y-%m-%d %H:%M")
                    }
                    processed_sources.append(source_info)
                
                # Cleanup
                os.unlink(temp_path)
                
            except Exception as e:
                if 'temp_path' in locals():
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                raise HTTPException(status_code=500, detail=f"Failed to process {uploaded_file.filename}: {str(e)}")
        
        return StandardResponse(
            status_code=200,
            status=True,
            message=f"Processed {len(processed_sources)} file(s) successfully",
            data={"sources": processed_sources},
            path="/api/documents/upload"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/urls", response_model=StandardResponse)
async def process_urls(
    request: URLsRequest,
    current_user: User = Depends(get_current_user)
):
    urls = request.urls
    """Process website URLs"""
    components = get_pipeline_components()
    
    # Use .get() to safely access web_scraper key
    if not components.get('web_scraper'):
        raise HTTPException(
            status_code=400,
            detail="Web scraping not available (missing FIRECRAWL_API_KEY)"
        )
    
    processed_sources = []
    
    try:
        for url in urls:
            if not url.strip():
                continue
                
            chunks = components['web_scraper'].scrape_url(url.strip())
            
            if chunks:
                for chunk in chunks:
                    chunk.source_file = url
                
                embedded_chunks = components['embedding_generator'].generate_embeddings(chunks)
                
                if len(processed_sources) == 0:
                    components['vector_db'].create_index(use_binary_quantization=False)
                
                # Insert embeddings with user_id for user-specific isolation
                user_id = str(current_user.id)
                components['vector_db'].insert_embeddings(embedded_chunks, user_id=user_id)
                
                source_info = {
                    'name': url,
                    'type': "Website",
                    'size': f"{len(chunks)} chunks",
                    'chunks': len(chunks),
                    'uploaded_at': time.strftime("%Y-%m-%d %H:%M")
                }
                processed_sources.append(source_info)
        
        return StandardResponse(
            status_code=200,
            status=True,
            message=f"Processed {len(processed_sources)} URL(s) successfully",
            data={"sources": processed_sources},
            path="/api/documents/urls"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error for debugging
        logger.error(f"URL processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process URLs. Please try again later."
        )

@router.post("/youtube", response_model=StandardResponse)
async def process_youtube(
    request: YouTubeRequest,
    current_user: User = Depends(get_current_user)
):
    url = request.url
    """Process YouTube video"""
    components = get_pipeline_components()
    
    if not components['youtube_transcriber']:
        raise HTTPException(
            status_code=400,
            detail="YouTube processing not available (missing ASSEMBLYAI_API_KEY)"
        )
    
    try:
        transcriber = components['youtube_transcriber']
        chunks = transcriber.transcribe_youtube_video(url, cleanup_audio=True)
        
        if chunks:
            video_id = transcriber.extract_video_id(url)
            video_name = f"YouTube Video {video_id}"
            
            for chunk in chunks:
                chunk.source_file = video_name
            
            embedded_chunks = components['embedding_generator'].generate_embeddings(chunks)
            components['vector_db'].create_index(use_binary_quantization=False)
            
            # Insert embeddings with user_id for user-specific isolation
            user_id = str(current_user.id)
            components['vector_db'].insert_embeddings(embedded_chunks, user_id=user_id)
            
            source_info = {
                'name': video_name,
                'type': "YouTube Video",
                'size': f"{len(chunks)} utterances",
                'chunks': len(chunks),
                'uploaded_at': time.strftime("%Y-%m-%d %H:%M"),
                'url': url,
                'video_id': video_id
            }
            
            return StandardResponse(
                status_code=200,
                status=True,
                message=f"Processed YouTube video: {len(chunks)} utterances",
                data={"source": source_info},
                path="/api/documents/youtube"
            )
        else:
            raise HTTPException(status_code=400, detail="No transcript content extracted from the video")
            
    except ValueError as e:
        error_msg = str(e)
        if "API key" in error_msg:
            raise HTTPException(status_code=400, detail="Invalid AssemblyAI API key")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YouTube processing failed: {str(e)}")

@router.post("/text", response_model=StandardResponse)
async def process_text(
    request: TextRequest,
    current_user: User = Depends(get_current_user)
):
    text = request.text
    title = request.title
    """Process pasted text"""
    components = get_pipeline_components()
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text content is required")
    
    try:
        # Save text to temp file
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as tmp_file:
            tmp_file.write(text)
            temp_path = tmp_file.name
        
        chunks = components['doc_processor'].process_document(temp_path)
        
        original_name = title or f"Pasted Text ({time.strftime('%H:%M')})"
        for chunk in chunks:
            chunk.source_file = original_name
        
        if chunks:
            embedded_chunks = components['embedding_generator'].generate_embeddings(chunks)
            components['vector_db'].create_index(use_binary_quantization=False)
            
            # Insert embeddings with user_id for user-specific isolation
            user_id = str(current_user.id)
            components['vector_db'].insert_embeddings(embedded_chunks, user_id=user_id)
            
            source_info = {
                'name': original_name,
                'type': "Text",
                'size': f"{len(text)} chars",
                'chunks': len(chunks),
                'uploaded_at': time.strftime("%Y-%m-%d %H:%M")
            }
            
            os.unlink(temp_path)
            
            return StandardResponse(
                status_code=200,
                status=True,
                message=f"Processed text: {len(chunks)} chunks",
                data={"source": source_info},
                path="/api/documents/text"
            )
        else:
            os.unlink(temp_path)
            raise HTTPException(status_code=400, detail="No content extracted from text")
            
    except Exception as e:
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Text processing failed: {str(e)}")

@router.get("/sources", response_model=StandardResponse)
async def get_sources(
    current_user: User = Depends(get_current_user)
):
    """Get all sources from vector database"""
    components = get_pipeline_components()
    
    try:
        # Get all points from the collection to extract unique sources
        # Use scroll to get all points with their payloads
        from qdrant_client.models import ScrollRequest
        
        vector_db = components['vector_db']
        collection_name = vector_db.collection_name
        
        # Get user_id for filtering
        user_id = str(current_user.id)
        
        # Scroll through all points to get unique sources, filtered by user_id
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        query_filter = Filter(
            must=[
                FieldCondition(key="user_id", match=MatchValue(value=user_id))
            ]
        )
        
        scroll_result = vector_db.client.scroll(
            collection_name=collection_name,
            scroll_filter=query_filter,
            limit=10000,  # Get a large batch
            with_payload=True,
            with_vectors=False
        )
        
        # Extract unique sources from payloads
        sources_map = {}
        points = scroll_result[0]  # First element is the list of points
        
        for point in points:
            payload = point.payload
            
            # Additional safety check: skip if user_id doesn't match
            if payload.get('user_id') != user_id:
                continue
            
            source_file = payload.get('source_file', 'Unknown')
            
            if source_file not in sources_map:
                sources_map[source_file] = {
                    'name': source_file,
                    'type': payload.get('source_type', 'Document'),
                    'chunks': 0,
                    'uploaded_at': None
                }
            
            sources_map[source_file]['chunks'] += 1
        
        # Convert to list
        sources_list = list(sources_map.values())
        
        return StandardResponse(
            status_code=200,
            status=True,
            message="Sources retrieved successfully",
            data={"sources": sources_list},
            path="/api/documents/sources"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving sources: {str(e)}")
        # Return empty list on error rather than failing
        return StandardResponse(
            status_code=200,
            status=True,
            message="Sources retrieved successfully",
            data={"sources": []},
            path="/api/documents/sources"
        )

@router.delete("/sources/{source_name:path}", response_model=StandardResponse)
async def delete_source(
    source_name: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a source and all its chunks from the vector database"""
    components = get_pipeline_components()
    
    try:
        vector_db = components['vector_db']
        user_id = str(current_user.id)
        
        # Delete all points for this source and user
        deleted_count = vector_db.delete_source(source_name, user_id=user_id)
        
        if deleted_count == 0:
            return StandardResponse(
                status_code=404,
                status=False,
                message=f"Source '{source_name}' not found",
                data={"deleted_count": 0},
                path=f"/api/documents/sources/{source_name}"
            )
        
        return StandardResponse(
            status_code=200,
            status=True,
            message=f"Source '{source_name}' deleted successfully",
            data={"deleted_count": deleted_count, "source_name": source_name},
            path=f"/api/documents/sources/{source_name}"
        )
        
    except Exception as e:
        logger.error(f"Error deleting source {source_name} for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete source: {str(e)}"
        )

