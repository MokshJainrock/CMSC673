"""Backward-compatible data loader for the original baseline script."""

from textbook_search.loader import load_corpus


def get_corpus():
    documents = load_corpus()
    docs = [document.searchable_text for document in documents]
    ids = [document.doc_id for document in documents]
    return ids, docs
