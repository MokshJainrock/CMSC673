#USING just a sample data right now will change later once Im done
corpus = [
    {"id": "bio_ch8_1", "text": "Photosynthesis converts light energy into chemical energy in chloroplasts. The light-dependent reactions occur in thylakoid membranes."},
    {"id": "bio_ch8_2", "text": "Cellular respiration breaks down glucose to produce ATP in mitochondria through glycolysis, Krebs cycle, and oxidative phosphorylation."},
    {"id": "bio_ch7_1", "text": "Mitosis is cell division that produces two identical daughter cells and consists of prophase, metaphase, anaphase, and telophase."},
    {"id": "chem_ch4_1", "text": "Acids donate protons in solution while bases accept protons according to Bronsted-Lowry theory."},
    {"id": "phys_ch2_1", "text": "Newton's second law states that force equals mass times acceleration, F = ma."},
]

def get_corpus():
    docs = [d["text"] for d in corpus]
    ids = [d["id"] for d in corpus]
    return ids, docs
