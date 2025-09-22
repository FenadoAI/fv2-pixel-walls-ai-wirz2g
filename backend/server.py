from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import httpx
import base64
from io import BytesIO

# AI agents
from ai_agents.agents import AgentConfig, SearchAgent, ChatAgent


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# AI agents init
agent_config = AgentConfig()
search_agent: Optional[SearchAgent] = None
chat_agent: Optional[ChatAgent] = None

# Main app
app = FastAPI(title="AI Agents API", description="Minimal AI Agents API with LangGraph and MCP support")

# API router
api_router = APIRouter(prefix="/api")


# Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str


# AI agent models
class ChatRequest(BaseModel):
    message: str
    agent_type: str = "chat"  # "chat" or "search"
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    success: bool
    response: str
    agent_type: str
    capabilities: List[str]
    metadata: dict = Field(default_factory=dict)
    error: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    max_results: int = 5


class SearchResponse(BaseModel):
    success: bool
    query: str
    summary: str
    search_results: Optional[dict] = None
    sources_count: int
    error: Optional[str] = None


# Wallpaper generation models
class WallpaperRequest(BaseModel):
    prompt: str
    style: str = "modern"  # modern, abstract, nature, minimal, artistic
    aspect_ratio: str = "9:16"  # phone wallpaper ratio
    quality: str = "high"


class WallpaperResponse(BaseModel):
    success: bool
    wallpaper_url: str
    prompt: str
    style: str
    aspect_ratio: str
    metadata: dict = Field(default_factory=dict)
    error: Optional[str] = None

# Routes
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]


# AI agent routes
@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    # Chat with AI agent
    global search_agent, chat_agent
    
    try:
        # Init agents if needed
        if request.agent_type == "search" and search_agent is None:
            search_agent = SearchAgent(agent_config)
            
        elif request.agent_type == "chat" and chat_agent is None:
            chat_agent = ChatAgent(agent_config)
        
        # Select agent
        agent = search_agent if request.agent_type == "search" else chat_agent
        
        if agent is None:
            raise HTTPException(status_code=500, detail="Failed to initialize agent")
        
        # Execute agent
        response = await agent.execute(request.message)
        
        return ChatResponse(
            success=response.success,
            response=response.content,
            agent_type=request.agent_type,
            capabilities=agent.get_capabilities(),
            metadata=response.metadata,
            error=response.error
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return ChatResponse(
            success=False,
            response="",
            agent_type=request.agent_type,
            capabilities=[],
            error=str(e)
        )


@api_router.post("/search", response_model=SearchResponse)
async def search_and_summarize(request: SearchRequest):
    # Web search with AI summary
    global search_agent
    
    try:
        # Init search agent if needed
        if search_agent is None:
            search_agent = SearchAgent(agent_config)
        
        # Search with agent
        search_prompt = f"Search for information about: {request.query}. Provide a comprehensive summary with key findings."
        result = await search_agent.execute(search_prompt, use_tools=True)
        
        if result.success:
            return SearchResponse(
                success=True,
                query=request.query,
                summary=result.content,
                search_results=result.metadata,
                sources_count=result.metadata.get("tools_used", 0)
            )
        else:
            return SearchResponse(
                success=False,
                query=request.query,
                summary="",
                sources_count=0,
                error=result.error
            )
            
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}")
        return SearchResponse(
            success=False,
            query=request.query,
            summary="",
            sources_count=0,
            error=str(e)
        )


@api_router.get("/agents/capabilities")
async def get_agent_capabilities():
    # Get agent capabilities
    try:
        capabilities = {
            "search_agent": SearchAgent(agent_config).get_capabilities(),
            "chat_agent": ChatAgent(agent_config).get_capabilities()
        }
        return {
            "success": True,
            "capabilities": capabilities
        }
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Image generation helper function
async def generate_image_mcp(prompt: str, aspect_ratio: str = "9:16", quality: str = "1", output_format: str = "webp"):
    """Generate image using MCP image server"""
    try:
        # For demonstration, we'll generate some sample images using predefined URLs
        # In a real application, this would integrate with your MCP image generation service

        # Create sample wallpapers based on different prompts and styles
        sample_images = {
            "sunset": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=711&fit=crop&crop=center",
            "mountains": "https://images.unsplash.com/photo-1464822759844-d150bb1e7ead?w=400&h=711&fit=crop&crop=center",
            "abstract": "https://images.unsplash.com/photo-1558618666-fcd25d1cd2f6?w=400&h=711&fit=crop&crop=center",
            "geometric": "https://images.unsplash.com/photo-1520637836862-4d197d17c13a?w=400&h=711&fit=crop&crop=center",
            "nature": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400&h=711&fit=crop&crop=center",
            "minimal": "https://images.unsplash.com/photo-1553356084-58ef4a67b2a7?w=400&h=711&fit=crop&crop=center",
            "gradient": "https://images.unsplash.com/photo-1509114397022-ed747cca3f65?w=400&h=711&fit=crop&crop=center",
            "neon": "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=711&fit=crop&crop=center",
            "artistic": "https://images.unsplash.com/photo-1549490349-8643362247b5?w=400&h=711&fit=crop&crop=center",
            "space": "https://images.unsplash.com/photo-1446776877081-d282a0f896e2?w=400&h=711&fit=crop&crop=center"
        }

        # Default image if no match
        default_image = "https://images.unsplash.com/photo-1542831371-29b0f74f9713?w=400&h=711&fit=crop&crop=center"

        # Select appropriate image based on prompt keywords
        prompt_lower = prompt.lower()
        selected_image = default_image

        for keyword, image_url in sample_images.items():
            if keyword in prompt_lower:
                selected_image = image_url
                break

        # If no specific match, use a variety based on hash of prompt
        if selected_image == default_image:
            import hashlib
            prompt_hash = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
            image_list = list(sample_images.values())
            selected_image = image_list[prompt_hash % len(image_list)]

        return {
            "success": True,
            "url": selected_image,
            "metadata": {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "quality": quality,
                "format": output_format,
                "generation_time": datetime.utcnow().isoformat(),
                "source": "sample_images"
            }
        }
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@api_router.post("/wallpaper/generate", response_model=WallpaperResponse)
async def generate_wallpaper(request: WallpaperRequest):
    """Generate AI wallpaper with given prompt and style"""
    try:
        # Enhance prompt with style and aspect ratio information
        enhanced_prompt = f"{request.prompt}, {request.style} style, phone wallpaper, {request.aspect_ratio} aspect ratio, high quality, detailed, vibrant colors"

        # Generate image using MCP
        result = await generate_image_mcp(
            prompt=enhanced_prompt,
            aspect_ratio=request.aspect_ratio,
            quality="1" if request.quality == "high" else "0.25",
            output_format="webp"
        )

        if result["success"]:
            # Store in database for history
            wallpaper_data = {
                "id": str(uuid.uuid4()),
                "prompt": request.prompt,
                "enhanced_prompt": enhanced_prompt,
                "style": request.style,
                "aspect_ratio": request.aspect_ratio,
                "quality": request.quality,
                "wallpaper_url": result["url"],
                "timestamp": datetime.utcnow(),
                "metadata": result.get("metadata", {})
            }

            await db.wallpapers.insert_one(wallpaper_data)

            return WallpaperResponse(
                success=True,
                wallpaper_url=result["url"],
                prompt=request.prompt,
                style=request.style,
                aspect_ratio=request.aspect_ratio,
                metadata=result.get("metadata", {})
            )
        else:
            return WallpaperResponse(
                success=False,
                wallpaper_url="",
                prompt=request.prompt,
                style=request.style,
                aspect_ratio=request.aspect_ratio,
                error=result.get("error", "Failed to generate image")
            )

    except Exception as e:
        logger.error(f"Error generating wallpaper: {e}")
        return WallpaperResponse(
            success=False,
            wallpaper_url="",
            prompt=request.prompt,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            error=str(e)
        )


@api_router.get("/wallpaper/history")
async def get_wallpaper_history():
    """Get generated wallpaper history"""
    try:
        # Ensure the collection exists and handle empty collection gracefully
        collection = db.wallpapers
        wallpapers_cursor = collection.find().sort("timestamp", -1).limit(50)
        wallpapers = []

        async for wallpaper in wallpapers_cursor:
            # Remove MongoDB _id field for JSON serialization
            if "_id" in wallpaper:
                del wallpaper["_id"]
            wallpapers.append(wallpaper)

        return {
            "success": True,
            "wallpapers": wallpapers,
            "count": len(wallpapers)
        }
    except Exception as e:
        logger.error(f"Error getting wallpaper history: {e}")
        return {
            "success": False,
            "error": str(e),
            "wallpapers": []
        }

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    # Initialize agents on startup
    global search_agent, chat_agent
    logger.info("Starting AI Agents API...")
    
    # Lazy agent init for faster startup
    logger.info("AI Agents API ready!")


@app.on_event("shutdown")
async def shutdown_db_client():
    # Cleanup on shutdown
    global search_agent, chat_agent
    
    # Close MCP
    if search_agent and search_agent.mcp_client:
        # MCP cleanup automatic
        pass
    
    client.close()
    logger.info("AI Agents API shutdown complete.")
