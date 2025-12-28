"""Chat and RAG routes"""
import os
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas import StandardResponse

# Import RAG modules
from src.generation.rag import RAGGenerator
from src.embeddings.embedding_generator import EmbeddingGenerator
from src.memory.memory_layer import NotebookMemoryLayer
from app.routes.documents import get_pipeline_components

router = APIRouter()

# Initialize RAG components (singleton pattern)
_rag_components = {}

def get_rag_components():
    """Get or initialize RAG components"""
    if not _rag_components:
        openrouter_key = os.getenv('OPEN_ROUTER_API_KEY')
        if not openrouter_key:
            raise HTTPException(
                status_code=500,
                detail="OPEN_ROUTER_API_KEY not configured"
            )
        
        # Get singleton components to avoid multiple Qdrant client instances
        components = get_pipeline_components()
        embedding_generator = components['embedding_generator']
        vector_db = components['vector_db']
        
        _rag_components['rag_generator'] = RAGGenerator(
            embedding_generator=embedding_generator,
            vector_db=vector_db,
            openrouter_api_key=openrouter_key,
            model_name="openai/gpt-4o-mini",
            temperature=0.1
        )
        
        # Optional memory layer
        zep_key = os.getenv('ZEP_API_KEY')
        if zep_key:
            _rag_components['memory'] = NotebookMemoryLayer(
                user_id="api_user",
                session_id="default",
                create_new_session=True
            )
        else:
            _rag_components['memory'] = None
    
    return _rag_components

class ChatMessageRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

@router.post("/message", response_model=StandardResponse)
async def send_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a chat message and get RAG response"""
    components = get_rag_components()
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query is required")
    
    try:
        # Generate RAG response (filtered by user_id for user-specific isolation)
        user_id = str(current_user.id)
        result = components['rag_generator'].generate_response(request.query, user_id=user_id)
        
        # Format sources for response
        sources_info = []
        for source in result.sources_used:
            source_data = {
                'source_file': source.get('source_file', 'Unknown'),
                'source_type': source.get('source_type', 'unknown'),
                'page_number': source.get('page_number'),
                'chunk_id': source.get('chunk_id'),
                'content': source.get('content', '')[:300]  # Preview
            }
            sources_info.append(source_data)
        
        # Save to memory if available
        if components['memory']:
            components['memory'].save_conversation_turn(result)
        
        # Create citations list
        citations = []
        for source in result.sources_used:
            cite_text = f"Source: {source.get('source_file', 'Unknown')}"
            if source.get('page_number'):
                cite_text += f", Page: {source['page_number']}"
            citations.append(cite_text)
        
        return StandardResponse(
            status_code=200,
            status=True,
            message="Response generated successfully",
            data={
                "response": result.response,
                "sources": sources_info,
                "citations": citations,
                "retrieval_count": result.retrieval_count
            },
            path="/api/chat/message"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")

@router.get("/history/{session_id}", response_model=StandardResponse)
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get chat history for a session"""
    # TODO: Implement chat history retrieval from memory layer
    return StandardResponse(
        status_code=200,
        status=True,
        message="Chat history retrieved",
        data={"messages": []},
        path=f"/api/chat/history/{session_id}"
    )

