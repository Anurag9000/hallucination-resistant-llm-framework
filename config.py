import os

# Manual .env loader for environment stability
def load_env_manual():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

load_env_manual()

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
