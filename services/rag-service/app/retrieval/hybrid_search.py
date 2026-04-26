from typing import List, Dict, Any
import re

def keyword_score(query: str, document: str) -> float:
    """Simple BM25-like keyword scoring"""
    query_terms = set(re.findall(r'\w+', query.lower()))
    doc_terms = re.findall(r'\w+', document.lower())
    doc_term_set = set(doc_terms)
    
    if not query_terms or not doc_terms:
        return 0.0
    
    matches = query_terms.intersection(doc_term_set)
    return len(matches) / len(query_terms)

def hybrid_rerank(results: List[Dict[str, Any]], query: str, alpha: float = 0.7) -> List[Dict[str, Any]]:
    """Combine vector similarity with keyword matching"""
    for r in results:
        vector_score = r.get("score", 0)
        kw_score = keyword_score(query, r.get("content", ""))
        r["hybrid_score"] = alpha * vector_score + (1 - alpha) * kw_score
    
    return sorted(results, key=lambda x: x["hybrid_score"], reverse=True)
