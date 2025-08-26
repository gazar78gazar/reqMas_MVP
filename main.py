# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager
import logging
import asyncio

# Phase 2 imports
from phase2.orchestrator import Phase2Orchestrator
from src.state.crdt_state_manager import CRDTStateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize state manager and orchestrator as globals
state_manager = None
phase2_orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize Phase 2 components on startup"""
    global phase2_orchestrator, state_manager
    
    # Startup code
    logger.info("Starting Phase 2 system...")
    
    # Create adapter for state manager if needed
    class StateAdapter(CRDTStateManager):
        def __init__(self, session_id: str = "main"):
            super().__init__(session_id=session_id, mutex_config={})
            
        def get_active_constraints(self):
            """Get list of active constraint IDs"""
            snapshot = self.get_snapshot()
            return list(snapshot.constraints.keys()) if snapshot.constraints else []
        
        def add_constraint(self, constraint_id: str):
            """Add a constraint by ID"""
            from src.state.crdt_state_manager import Constraint, ConstraintStrength
            import time
            constraint = Constraint(
                id=constraint_id,
                value=None,
                strength=ConstraintStrength.MANDATORY,
                timestamp=time.time(),
                source_agent="phase2",
                confidence=1.0
            )
            super().add_constraint(constraint)
        
        def add_requirement(self, requirement: dict):
            """Add a requirement"""
            # This would need to be implemented based on your state structure
            pass
        
        def update_uc_probabilities(self, probs: dict):
            """Update UC probabilities"""
            for uc_id, prob in probs.items():
                self.add_use_case_signal(uc_id, prob, "phase2")
        
        def get_state(self):
            """Get current state as dict"""
            snapshot = self.get_snapshot()
            return {
                "constraints": [c.id for c in snapshot.constraints.values()],
                "use_cases": dict(snapshot.use_cases),
                "resolutions": len(snapshot.resolutions),
                "version": snapshot.version
            }
        
        def reset(self):
            """Reset the state"""
            self.__init__(session_id="main")
    
    state_manager = StateAdapter()
    phase2_orchestrator = Phase2Orchestrator(state_manager)
    
    logger.info("Phase 2 Orchestrator initialized")
    logger.info("System ready for processing")
    
    yield  # Application runs
    
    # Shutdown code (if needed)
    logger.info("Shutting down Phase 2 system...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="reqMAS Phase 2 API", 
    version="2.0.0",
    lifespan=lifespan  # Add lifespan here
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ProcessRequest(BaseModel):
    input: str
    session_id: str
    user_response: Optional[str] = None
    context: Optional[Dict] = None
    expertise_level: Optional[str] = "unknown"

class ProcessResponse(BaseModel):
    status: str
    confidence: float
    uc_probabilities: Dict
    abq_question: Optional[Dict] = None
    conflicts: Optional[List] = None
    resolution: Optional[str] = None
    state: Optional[Dict] = None
    message: Optional[str] = None

@app.post("/process", response_model=ProcessResponse)
async def process_input(request: ProcessRequest):
    """Main processing endpoint with Phase 2 capabilities"""
    try:
        # Handle A/B question response if provided
        if request.user_response and request.context:
            response = phase2_orchestrator.process_user_response(
                request.user_response,
                request.context
            )
            logger.info(f"Processed A/B response: {response}")
        
        # Main processing
        result = await phase2_orchestrator.process(
            request.input,
            request.session_id
        )
        
        # Build response based on result
        if result.needs_disambiguation:
            return ProcessResponse(
                status="needs_clarification",
                confidence=result.aggregated_confidence,
                uc_probabilities=result.uc_probabilities,
                abq_question=result.abq_question,
                message="Please answer the question to proceed"
            )
        
        elif result.conflicts_detected:
            conflicts_explained = []
            if result.conflicts_detected:
                for conflict in result.conflicts_detected:
                    if hasattr(conflict, 'explanation'):
                        conflicts_explained.append(conflict.explanation)
                    else:
                        conflicts_explained.append(str(conflict))
            
            return ProcessResponse(
                status="conflict_detected",
                confidence=result.aggregated_confidence,
                uc_probabilities=result.uc_probabilities,
                conflicts=conflicts_explained,
                resolution=result.suggested_resolution,
                abq_question=result.abq_question,
                message="Conflict detected - resolution required"
            )
        
        elif result.auto_resolve:
            return ProcessResponse(
                status="auto_resolved",
                confidence=result.aggregated_confidence,
                uc_probabilities=result.uc_probabilities,
                resolution=result.suggested_resolution,
                state=state_manager.get_state(),
                message="Conflict automatically resolved based on confidence"
            )
        
        else:
            return ProcessResponse(
                status="success",
                confidence=result.aggregated_confidence,
                uc_probabilities=result.uc_probabilities,
                state=state_manager.get_state(),
                message="Requirements processed successfully"
            )
            
    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Get current system status"""
    if phase2_orchestrator:
        return {
            "status": "initialized",
            "phase": "2",
            "components": {
                "bayesian_network": hasattr(phase2_orchestrator, 'bayesian_net'),
                "confidence_aggregator": hasattr(phase2_orchestrator, 'confidence_agg'),
                "dependency_graph": hasattr(phase2_orchestrator, 'dep_graph')
            },
            "state": state_manager.get_state() if state_manager else None
        }
    return {"status": "not_initialized"}

@app.post("/reset")
async def reset_system():
    """Reset the system state"""
    if state_manager:
        state_manager.reset()
    if phase2_orchestrator and hasattr(phase2_orchestrator, 'bayesian_net'):
        phase2_orchestrator.bayesian_net.reset_beliefs()
    return {"status": "reset_complete"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "phase": "2"}

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "reqMAS Phase 2 API",
        "version": "2.0.0",
        "endpoints": [
            "/process - Main processing endpoint",
            "/status - Get system status",
            "/reset - Reset system state",
            "/health - Health check",
            "/docs - Interactive API documentation"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    # For development with reload, use: python run_dev.py
    # For production or testing without reload:
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # No reload warning
        log_level="info"
    )