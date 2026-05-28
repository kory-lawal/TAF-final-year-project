import random

def generate_oriki(oriki_list):
    # Safely handle small lists and empty inputs
    if not oriki_list:
        return ""
    n = min(2, len(oriki_list))
    return " ".join(random.sample(oriki_list, n))