import timeit
import random
from nlp_engine import nlp, VernacularParser

def run_benchmark():
    test_sentences = [
        "I need a blood pack urgently in Dadar-East ke paas",
        "We are running out of clean water and food supplies near St. Jude's",
        "Oxygen cylinder required immediately for a critical patient",
        "Send some medicines and a first aid kit to the camp",
        "Insulin stock is low",
        "No issues at the moment",
        "Please send vaccines and paracetamol asap",
    ] * 1000 # 7000 sentences

    start_time = timeit.default_timer()
    for sentence in test_sentences:
        nlp.extract_entities(sentence)
    end_time = timeit.default_timer()

    print(f"Total time for 7000 extractions: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    run_benchmark()
