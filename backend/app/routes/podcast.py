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
        tts_generator = None
        tts_error_type = None
        try:
            tts_generator = PodcastTTSGenerator()
            tts_available = True
            logger.info("TTS generator initialized successfully")
        except ImportError as e:
            error_msg = str(e)
            logger.warning(f"TTS not available (ImportError): {error_msg}")
            tts_available = False
            tts_generator = None
            if "apex" in error_msg.lower() or "cannot import name 'amp'" in error_msg:
                logger.warning("TTS conflict detected: apex-saas-framework conflicts with TTS's apex dependency.")
                logger.warning("Solution: TTS requires NVIDIA apex for some features, but it conflicts with apex-saas-framework.")
                logger.warning("You may need to use a different TTS library or install NVIDIA apex in a separate environment.")
                tts_error_type = "apex_conflict"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to initialize TTS: {error_msg}", exc_info=True)
            tts_available = False
            tts_generator = None
            if "apex" in error_msg.lower():
                logger.error("TTS initialization failed due to apex package conflict.")
                tts_error_type = "apex_conflict"
        
        # Generate audio if TTS is available
        audio_urls = None
        if tts_available and tts_generator:
            logger.info("Starting audio generation (this may take a few minutes for long scripts)...")
            from datetime import datetime
            
            # Create a persistent output directory in backend/outputs/podcast_audio
            backend_dir = Path(__file__).parent.parent.parent
            outputs_dir = backend_dir / "outputs" / "podcast_audio"
            outputs_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a unique directory for this podcast
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            podcast_dir = outputs_dir / f"podcast_{timestamp}"
            podcast_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                audio_files = tts_generator.generate_podcast_audio(
                    podcast_script=podcast_script,
                    output_dir=str(podcast_dir),
                    combine_audio=True,
                    skip_individual_files=True  # Skip individual files for faster generation
                )
                logger.info(f"Generated {len(audio_files) if audio_files else 0} audio files")
                
                # Convert file paths to accessible URLs
                # Prioritize the combined podcast file (complete_podcast.wav) which contains all speakers
                if audio_files:
                    if isinstance(audio_files, list):
                        # Look for complete_podcast.wav first (contains all speakers' content)
                        combined_file = next((f for f in audio_files if 'complete_podcast.wav' in str(f)), None)
                        if combined_file:
                            filename = Path(combined_file).name
                            audio_urls = [f"/api/podcast/audio/{filename}"]
                            logger.info(f"Using combined audio file with all speakers: {filename}")
                        else:
                            # Fallback: Use the last file (should be the combined one if combine_audio=True)
                            last_file = audio_files[-1] if audio_files else None
                            if last_file:
                                filename = Path(last_file).name
                                audio_urls = [f"/api/podcast/audio/{filename}"]
                                logger.warning(f"Combined file not found, using last file: {filename}")
                    else:
                        filename = Path(audio_files).name
                        audio_urls = [f"/api/podcast/audio/{filename}"]
                        logger.info(f"Using single audio file: {filename}")
            except Exception as e:
                logger.error(f"Failed to generate audio: {str(e)}", exc_info=True)
                audio_files = None
                audio_urls = None
                tts_available = False
        
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
                "audio_files": audio_urls if audio_urls else None,
                "audio_file_count": len(audio_files) if audio_files else 0,
                "script_segments": podcast_script.total_lines,
                "tts_error": tts_error_type
            },
            path="/api/podcast/generate"
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        # Handle script generation errors (e.g., JSON parsing failures)
        error_msg = str(e)
        logger.error(f"Podcast script generation failed: {error_msg}", exc_info=True)
        if "Could not parse LLM response" in error_msg or "Invalid script format" in error_msg:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate podcast script. The AI response was invalid. Please try again. Error: {error_msg}"
            )
        else:
            raise HTTPException(status_code=500, detail=f"Podcast generation failed: {error_msg}")
    except Exception as e:
        # Log the full error for debugging
        error_msg = str(e)
        logger.error(f"Podcast generation failed: {error_msg}", exc_info=True)
        
        # Provide more user-friendly error messages
        if "TTS" in error_msg or "apex" in error_msg.lower():
            # TTS-related errors - script was generated but audio failed
            raise HTTPException(
                status_code=500,
                detail="Podcast script generated successfully, but audio generation failed. The script is available, but audio is not available due to TTS configuration issues."
            )
        elif "No content found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=500, detail=f"Podcast generation failed: {error_msg}")

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
    outputs_dir = backend_dir / "outputs"
    podcast_audio_dir = outputs_dir / "podcast_audio"
    
    audio_file = None
    
    # First, check in the root outputs directory (for files saved directly there)
    root_file = outputs_dir / filename
    if root_file.exists() and root_file.is_file():
        audio_file = root_file
        logger.info(f"Found audio file in root outputs: {audio_file}")
    else:
        # Then check in podcast_audio subdirectories (most recent first)
        if podcast_audio_dir.exists():
            podcast_dirs = sorted([d for d in podcast_audio_dir.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
            
            for podcast_dir in podcast_dirs:
                potential_file = podcast_dir / filename
                if potential_file.exists():
                    audio_file = potential_file
                    logger.info(f"Found audio file in podcast directory: {audio_file}")
                    break
    
    if not audio_file or not audio_file.exists():
        logger.error(f"Audio file not found: {filename}. Searched in: {outputs_dir} and {podcast_audio_dir}")
        raise HTTPException(status_code=404, detail=f"Audio file not found: {filename}")
    
    return FileResponse(
        path=str(audio_file),
        media_type="audio/wav",
        filename=filename
    )

