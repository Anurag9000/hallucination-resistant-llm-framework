import asyncio
import argparse
import sys
from config import Config
from core.cache import VerificationCache
from core.verifier_engine import VerifierFactory

# Model Imports
from models.v1_edgecore.pipeline import EdgeCorePipeline
from models.v1_finalthought.pipeline import FinalThoughtPipeline
from models.v2_context_aware.pipeline import ContextAwarePipeline

async def main():
    parser = argparse.ArgumentParser(description="Hallucination-Resistant AI Framework")
    parser.add_argument("--model", type=str, required=True, choices=["v1", "v1.1", "v2"], 
                        help="Select model: v1 (EdgeCore), v1.1 (FinalThought), v2 (Context-Aware)")
    parser.add_argument("--query", type=str, default="What is the capital of Mars?", help="User query")
    parser.add_argument("--learn", type=str, help="For v2: Inject a fact into memory before running")
    parser.add_argument("--provider", type=str, default="ollama", choices=["ollama", "gemini"],
                        help="LLM provider backend")
    parser.add_argument("--model_name", type=str, default="qwen2.5:1.5b", help="Specific model tag (e.g., qwen2.5:1.5b, gemini-2.5-flash)")
    
    args = parser.parse_args()

    print(f"🚀 Initializing Framework with Model: {args.model}")
    
    # Provider Initialization
    if args.provider == "ollama":
        from core.ollama_llm import OllamaLLM
        model_name = args.model_name or "qwen2.5:1.5b"
        print(f"--- Connecting to Local Ollama ({model_name}) ---")
        llm = OllamaLLM(model_name=model_name)
    elif args.provider == "gemini":
        from core.gemini_llm import GeminiLLM
        model_name = args.model_name or "gemini-2.5-flash"
        print(f"--- Connecting to Remote Gemini ({model_name}) ---")
        llm = GeminiLLM(model_name=model_name)
    else:
        raise ValueError(f"Unsupported provider: {args.provider}. Use 'ollama' or 'gemini'.")

    # Shared Backbone Initialization
    cache = VerificationCache(ttl_seconds=Config.VERIFIER_CACHE_TTL)
    verifier_factory = VerifierFactory(llm, cache)
    
    pipeline = None
    
    if args.model == "v1":
        print("--- Loading EdgeCore v1.0 (Simulation) ---")
        pipeline = EdgeCorePipeline(llm)
        
    elif args.model == "v1.1":
        print("--- Loading Final Thought v1.1 (Interceptor Pipeline) ---")
        pipeline = FinalThoughtPipeline(llm, verifier_factory)
        
    elif args.model == "v2":
        print("--- Loading Context-Aware v2.1 (ULTIMA-X) ---")
        pipeline = ContextAwarePipeline(llm)
        if args.learn:
            print(f"📝 Learning new fact: {args.learn}")
            pipeline.learn_fact(args.learn)

    print(f"\n❓ Query: {args.query}")
    print("⏳ Processing...")
    
    try:
        if args.model == "v2":
            result = await pipeline.run(args.query)
        elif args.model == "v1.1":
            result = await pipeline.run(args.query)
        else:
            result = await pipeline.run(args.query)
            
        print(f"\n✅ Result:\n{result}")
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
