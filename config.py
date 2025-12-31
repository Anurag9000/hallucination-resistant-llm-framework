import os

class Config:
    DEBUG = True
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EVIDENCE_DIR = os.path.join(BASE_DIR, "evidence_data")
    
    # Model Simulation settings
    SIMULATION_LATENCY_MS = 50
    
    # Verifier Settings
    VERIFIER_CACHE_TTL = 3600  # 1 hour
    SCORE_THRESHOLD_VERIFIED = 0.85
    SCORE_THRESHOLD_LIKELY = 0.55
    
    # Context Settings
    MAX_SESSION_HISTORY = 10  # turns
