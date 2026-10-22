"""Reuse the typed compact schema and relationship validator, with explicit external semantics."""
from analysis.compact.preprocess import groups as reconstruct


def groups(trees,requested,layout,step_size='64 MB'):
    return reconstruct(trees,requested,layout,step_size,external=True)
