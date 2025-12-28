"""Podcast generation routes"""
import os
import logging
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas import StandardResponse

logger = logging.getLogger(__name__)

# Import podcast modules
from src.podcast.script_generator import PodcastScriptGenerator
from src.podcast.text_to_speech import PodcastTTSGenerator
from src.generation.rag import RAGGenerator
from src.embeddings.embedding_generator import EmbeddingGenerator
from app.routes.documents import get_pipeline_components

router = APIRouter()

# Store podcast jobs (in production, use Redis or database)
_podcast_jobs = {}

class PodcastRequest(BaseModel):
    source_name: str
    style: str
    length: str

@router.post("/generate", response_model=StandardResponse)
async def generate_podcast(
    request: PodcastRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Generate podcast script and audio"""
    openrouter_key = os.getenv('OPEN_ROUTER_API_KEY')
    if not openrouter_key:
        raise HTTPException(
            status_code=400,
            detail="Podcast generation not available (missing OPEN_ROUTER_API_KEY)"
        )
    
    try:
        # Get singleton components to avoid multiple Qdrant client instances
        components = get_pipeline_components()
        embedding_generator = components['embedding_generator']
        vector_db = components['vector_db']
        
        script_generator = PodcastScriptGenerator(
            openrouter_api_key=openrouter_key,
            model_name="openai/gpt-4o-mini"
        )
        
        # Search for source content from vector database (filtered by user_id)
        user_id = str(current_user.id)
        query_embedding = embedding_generator.generate_query_embedding(
            f"content from {request.source_name}"
        )
        search_results = vector_db.search(
            query_embedding,
            limit=50,
            filter_expr=f'source_file == "{request.source_name}"',
            user_id=user_id
        )
        
        if not search_results:
            raise HTTPException(
                status_code=404,
                detail=f"No content found for source: {request.source_name}"
            )
        
        # Convert search results to text content
        # search_results is a list of dictionaries with 'content' key
        text_content = "\n\n".join([result.get('content', '') for result in search_results if result.get('content')])
        
        # Generate podcast script from the retrieved text content
        podcast_script = script_generator.generate_script_from_text(
            text_content=text_content,
            source_name=request.source_name,
            podcast_style=request.style,
            target_duration=request.length
        )
        
        # Generate audio if TTS is available
        audio_files = None
        tts_available = False
        try:
            tts_generator = PodcastTTSGenerator()
            tts_available = True
        except:
            pass
        
        # Generate audio if TTS is available
        audio_urls = None
        if tts_available and tts_generator:
            from datetime import datetime
            
            # Create a persistent output directory in backend/outputs/podcast_audio
            backend_dir = Path(__file__).parent.parent.parent
            outputs_dir = backend_dir / "outputs" / "podcast_audio"
            outputs_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a unique directory for this podcast
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            podcast_dir = outputs_dir / f"podcast_{timestamp}"
            podcast_dir.mkdir(parents=True, exist_ok=True)
            
            audio_files = tts_generator.generate_podcast_audio(
                podcast_script=podcast_script,
                output_dir=str(podcast_dir),
                combine_audio=True
            )
            
            # Convert file paths to accessible URLs
            if audio_files:
                if isinstance(audio_files, list):
                    audio_urls = [f"/api/podcast/audio/{Path(f).name}" for f in audio_files]
                else:
                    audio_urls = [f"/api/podcast/audio/{Path(audio_files).name}"]
        
        # Determine source type
        source_type = "Document"
        if request.source_name.startswith("http"):
            source_type = "Website"
        elif "youtube" in request.source_name.lower() or "youtu.be" in request.source_name.lower():
            source_type = "YouTube Video"
        elif request.source_name.startswith("Pasted Text"):
            source_type = "Text"
        
        return StandardResponse(
            status_code=200,
            status=True,
            message="Podcast generated successfully",
            data={
                "script": podcast_script.to_json(),
                "script_metadata": {
                    "total_lines": podcast_script.total_lines,
                    "estimated_duration": podcast_script.estimated_duration,
                    "style": request.style,
                    "length": request.length,
                    "source_document": podcast_script.source_document,
                    "source_type": source_type
                },
                "audio_available": tts_available,
                "audio_files": audio_urls if audio_urls else None
            },
            path="/api/podcast/generate"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the full error for debugging
        logger.error(f"Podcast generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Podcast generation failed: {str(e)}")

@router.get("/status/{job_id}", response_model=StandardResponse)
async def get_podcast_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get podcast generation status"""
    if job_id not in _podcast_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return StandardResponse(
        status_code=200,
        status=True,
        message="Status retrieved",
        data=_podcast_jobs[job_id],
        path=f"/api/podcast/status/{job_id}"
    )

@router.get("/audio/{filename}")
async def get_podcast_audio(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Serve podcast audio files"""
    backend_dir = Path(__file__).parent.parent.parent
    outputs_dir = backend_dir / "outputs" / "podcast_audio"
    
    # Search for the file in all podcast directories
    audio_file = None
    for podcast_dir in outputs_dir.iterdir():
        if podcast_dir.is_dir():
            potential_file = podcast_dir / filename
            if potential_file.exists():
                audio_file = potential_file
                break
    
    if not audio_file or not audio_file.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=str(audio_file),
        media_type="audio/wav",
        filename=filename
    )

@router.get("/audio/{filename}")
async def get_podcast_audio(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Serve podcast audio files"""
    backend_dir = Path(__file__).parent.parent.parent
    outputs_dir = backend_dir / "outputs" / "podcast_audio"
    
    # Search for the file in all podcast directories
    audio_file = None
    for podcast_dir in outputs_dir.iterdir():
        if podcast_dir.is_dir():
            potential_file = podcast_dir / filename
            if potential_file.exists():
                audio_file = potential_file
                break
    
    if not audio_file or not audio_file.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=str(audio_file),
        media_type="audio/wav",
        filename=filename
    )

