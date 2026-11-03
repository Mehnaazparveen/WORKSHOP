"""
Smart Matching Engine for Campus Lost & Found.
Uses Scikit-learn TF-IDF Vectorizer and Cosine Similarity to compare
lost and found item reports based on descriptions, titles, categories,
colors, and locations.
"""

from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re


def build_item_text(item: Dict[str, Any]) -> str:
    """
    Constructs a rich composite text representation of an item,
    giving extra weight to title, category, and color.
    """
    title = (item.get("title") or "").strip()
    category = (item.get("category") or "").strip()
    color = (item.get("color") or "").strip()
    description = (item.get("description") or "").strip()
    location = (item.get("location") or "").strip()

    # Repeat title, category, and color to naturally weight them higher in TF-IDF
    tokens = [
        title,
        title,
        category,
        color,
        color,
        description,
        location,
    ]
    combined = " ".join(t for t in tokens if t)
    # Clean redundant whitespaces
    combined = re.sub(r"\s+", " ", combined)
    return combined.lower()


def compute_matches(
    lost_items: List[Dict[str, Any]],
    found_items: List[Dict[str, Any]],
    threshold: float = 0.20,
) -> List[Dict[str, Any]]:
    """
    Computes pairwise similarity scores between all provided lost and found items.
    Returns a sorted list of matches above the given similarity threshold.
    """
    if not lost_items or not found_items:
        return []

    lost_texts = [build_item_text(item) for item in lost_items]
    found_texts = [build_item_text(item) for item in found_items]

    # Combine all documents to build the corpus vocabulary
    all_texts = lost_texts + found_texts

    # TF-IDF Vectorizer configured with English stop words and n-grams (1, 2)
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        lowercase=True,
    )

    tfidf_matrix = vectorizer.fit_transform(all_texts)
    lost_vectors = tfidf_matrix[: len(lost_texts)]
    found_vectors = tfidf_matrix[len(lost_texts) :]

    # Pairwise cosine similarity matrix: shape (num_lost, num_found)
    similarity_matrix = cosine_similarity(lost_vectors, found_vectors)

    feature_names = vectorizer.get_feature_names_out()

    matches = []
    for i, lost_item in enumerate(lost_items):
        for j, found_item in enumerate(found_items):
            score = float(similarity_matrix[i, j])

            # Category boost/bonus: if category matches exactly, add confidence boost
            lost_cat = (lost_item.get("category") or "").strip().lower()
            found_cat = (found_item.get("category") or "").strip().lower()
            category_match = (lost_cat == found_cat) and (lost_cat != "")

            # If categories match, give a modest boost up to 1.0
            adjusted_score = score
            if category_match and score > 0.05:
                adjusted_score = min(1.0, score + 0.15)
            elif category_match and score == 0:
                # If both have the same category even if text differs slightly
                adjusted_score = 0.20

            if adjusted_score >= threshold:
                # Determine overlapping keyword features between this pair
                lost_row = lost_vectors[i].toarray()[0]
                found_row = found_vectors[j].toarray()[0]
                overlap_indices = (lost_row > 0) & (found_row > 0)
                shared_keywords = [
                    feature_names[idx]
                    for idx, is_overlap in enumerate(overlap_indices)
                    if is_overlap
                ][:5]

                matches.append(
                    {
                        "lost_item": lost_item,
                        "found_item": found_item,
                        "score": round(adjusted_score, 4),
                        "percentage": int(round(adjusted_score * 100)),
                        "shared_keywords": shared_keywords,
                        "category_match": category_match,
                    }
                )

    # Sort descending by match score
    matches.sort(key=lambda m: m["score"], reverse=True)
    return matches


def find_matches_for_item(
    target_item: Dict[str, Any],
    candidate_items: List[Dict[str, Any]],
    threshold: float = 0.15,
) -> List[Dict[str, Any]]:
    """
    Finds and ranks candidate items that match a specific target item.
    If target is 'lost', candidate_items should be 'found' items (and vice versa).
    """
    if not candidate_items:
        return []

    if target_item.get("type") == "lost":
        raw_matches = compute_matches([target_item], candidate_items, threshold=threshold)
        return [
            {
                "matched_item": m["found_item"],
                "score": m["score"],
                "percentage": m["percentage"],
                "shared_keywords": m["shared_keywords"],
                "category_match": m["category_match"],
            }
            for m in raw_matches
        ]
    else:
        raw_matches = compute_matches(candidate_items, [target_item], threshold=threshold)
        return [
            {
                "matched_item": m["lost_item"],
                "score": m["score"],
                "percentage": m["percentage"],
                "shared_keywords": m["shared_keywords"],
                "category_match": m["category_match"],
            }
            for m in raw_matches
        ]
