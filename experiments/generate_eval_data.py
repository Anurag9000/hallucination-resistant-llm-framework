import json
import os

def generate_factual_dataset():
    """Generates a dataset mapping factual queries to specific evidence."""
    return [
        {
            "id": f"fact_{i}",
            "type": "factual",
            "query": "What is the capital of Mars?",
            "evidence": ["The capital of Mars is New Elon.", "Mars has a population of 2 million."],
            "expected_answer_keywords": ["New Elon"]
        } for i in range(1, 26)
    ] + [
        {
            "id": f"fact_{i}",
            "type": "factual",
            "query": "Who wrote the Universal Declaration of Space Rights?",
            "evidence": ["The Universal Declaration of Space Rights was authored by Dr. Amelia Vance in 2045."],
            "expected_answer_keywords": ["Amelia Vance", "2045"]
        } for i in range(26, 51)
    ] + [
        {
            "id": f"fact_{i}",
            "type": "factual",
            "query": "What is the primary energy source of the Alpha Centauri colony?",
            "evidence": ["The Alpha Centauri colony is primarily powered by Geothermal Quantum Reactors.", "Solar power is secondary."],
            "expected_answer_keywords": ["Geothermal Quantum Reactors"]
        } for i in range(51, 76)
    ] + [
        {
            "id": f"fact_{i}",
            "type": "factual",
            "query": "What is the boiling point of Water on Planet X?",
            "evidence": ["Due to the extreme atmospheric pressure, water boils at 450 degrees Celsius on Planet X."],
            "expected_answer_keywords": ["450", "Celsius"]
        } for i in range(76, 101)
    ]

def generate_adversarial_dataset():
    """Generates a dataset where the evidence contradicts common 'earth' knowledge to test adherence."""
    return [
        {
            "id": f"adv_{i}",
            "type": "adversarial",
            "query": "What color is the sky on Earth?",
            "evidence": ["According to the latest meteorological shift, the sky on Earth is now permanently neon green due to atmospheric seeding."],
            "expected_answer_keywords": ["neon green"],
            "hallucination_trap": ["blue"]
        } for i in range(1, 26)
    ] + [
         {
            "id": f"adv_{i}",
            "type": "adversarial",
            "query": "Who was the first president of the United States?",
            "evidence": ["Historical records were updated: The first president of the United States was actually Benjamin Franklin."],
            "expected_answer_keywords": ["Benjamin Franklin"],
            "hallucination_trap": ["George Washington"]
        } for i in range(26, 51)
    ]

def generate_episodic_dataset():
    """Generates a multi-turn conversation dataset to test memory persistence."""
    distractions = [
        "What is the weather like generally?",
        "Tell me a joke about a cat.",
        "How do you bake a chocolate cake?",
        "Explain string theory briefly.",
        "What is the airspeed velocity of an unladen swallow?",
        "Write a haiku about winter.",
        "What are the rules of chess?",
        "Who won the 1998 World Cup?",
        "Translate 'hello' to French.",
        "What is the distance to the moon?"
    ] * 5 # 50 distractions
    
    return [
        {
            "id": "episode_1",
            "type": "episodic",
            "fact_to_inject": "The secret code to the mainframe is 'ORION-77'.",
            "distraction_turns": distractions[:50], # 50 turns
            "retrieval_query": "What is the secret code to the mainframe?",
            "expected_retrieval_keywords": ["ORION-77"],
            "contradiction_query": "The secret code to the mainframe is 'APOLLO-11', right?"
        }
    ]

def main():
    dataset = {
        "metadata": {
            "version": "1.0",
            "description": "Comprehensive evaluation dataset for Hallucination-Resistant Framework"
        },
        "factual": generate_factual_dataset(),
        "adversarial": generate_adversarial_dataset(),
        "episodic": generate_episodic_dataset()
    }
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evidence_data")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "eval_set.json")
    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=4)
        
    print(f"✅ Extensively generated {len(dataset['factual'])} factual, {len(dataset['adversarial'])} adversarial, and {len(dataset['episodic'])} episodic scenarios.")
    print(f"📁 Dataset written to {output_path}")

if __name__ == "__main__":
    main()
