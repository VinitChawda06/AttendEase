import streamlit as st
import re
from collections import Counter

class TextCorrector:
    def __init__(self):
        self.word_counts = Counter()
        self.load_dictionary()

    def load_dictionary(self):
        # In a real-world scenario, you'd load a comprehensive dictionary
        # For this example, we'll use a small set of common words
        words = """
        the and to of a in that is was he for it with as his on be at by I this had
        not are but from or have an they which one you were her all she there would
        their we him been has when who will more no if out so said what its about
        than up them can only other new some time could these two may then do first
        any my now such like our over man me even most made after also did many
        before must well back through years where much your way down should because
        long each just state people those too how little good world make very year
        still see own work men day get here old between both life being under three
        never know same last another while us off might great states go come since
        against right came take used himself few house use during without again
        place american home during small however asked large until along away shown
        went school important several high every idea really say once left open
        don't yet saw something united himself has few let under took government
        general part upon here point given
        """.split()
        self.word_counts.update(words)

    def correct_spelling(self, word):
        if word.lower() in self.word_counts:
            return word
        candidates = self.get_candidates(word)
        return max(candidates, key=lambda w: self.word_counts[w.lower()])

    def get_candidates(self, word):
        letters = 'abcdefghijklmnopqrstuvwxyz'
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
        inserts = [L + c + R for L, R in splits if len(L) < len(word) for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def correct_grammar(self, text):
        # This is a basic grammar correction
        # In a real-world scenario, you'd use more sophisticated NLP techniques
        text = re.sub(r'\bi\b', 'I', text)
        text = re.sub(r'\s+([.,:;!?])', r'\1', text)
        text = re.sub(r'([.!?])\s*([a-z])', lambda m: m.group(1) + ' ' + m.group(2).upper(), text)
        return text

    def correct_text(self, text):
        words = re.findall(r'\b\w+\b|\S', text)
        corrected_words = [self.correct_spelling(word) for word in words]
        corrected_text = ''.join(corrected_words)
        return self.correct_grammar(corrected_text)

def main():
    st.set_page_config(page_title="Text Correction App", page_icon="📝")
    st.title("Text Correction App")
    st.write("Enter your text below and see the corrected version!")

    corrector = TextCorrector()

    # Create a text area for input
    text_input = st.text_area("Your Text", height=200)

    if text_input:
        corrected_text = corrector.correct_text(text_input)

        # Display original and corrected text side by side
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Original Text")
            st.write(text_input)
        with col2:
            st.subheader("Corrected Text")
            st.write(corrected_text)

        # Display differences
        st.subheader("Corrections Made")
        original_words = re.findall(r'\b\w+\b|\S', text_input)
        corrected_words = re.findall(r'\b\w+\b|\S', corrected_text)
        
        for orig, corr in zip(original_words, corrected_words):
            if orig != corr:
                st.write(f"'{orig}' → '{corr}'")

if __name__ == "__main__":
    main()