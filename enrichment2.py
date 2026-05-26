"""
News Enrichment via Polza AI (OpenAI-compatible API) — OPTIMIZED VERSION
========================================================================
Optimized for cost:
  - Model: google/gemini-3.1-flash-lite
  - Batching: 4 articles per request
  - Truncation: 3000 chars per article
  - SMART FILTER: Only processes articles missing sentiment, entities, or concepts.

Analyzes article text AND title, adds:
  - Sentiment (label, score, confidence, emotion)
  - Named Entities (people, orgs, locations, events, etc.)
  - Main Concepts/Themes (abstract topics with salience)

API: https://polza.ai/api/v1/chat/completions

Prerequisites:
    pip install openai pydantic

Set your API key:
    export POLZA_AI_API_KEY="your_api_key_here"
"""

import json
import os
import time
import sys
from typing import Optional, List
from datetime import datetime

from openai import OpenAI


# =============================================================================
# CONFIGURATION
# =============================================================================
os.environ['POLZA_AI_API_KEY'] = "API"
INPUT_FILE = "final_holod_sentiment3.json"
OUTPUT_FILE = "AGAINholod_enriched3.json"

# Polza AI settings
API_BASE = "https://polza.ai/api/v1"
MODEL_NAME = "google/gemini-3.1-flash-lite"

# Batching: how many articles per API call
BATCH_SIZE = 4

# Rate limiting: seconds between API calls
DELAY_BETWEEN_CALLS = 0

# Maximum text length per article (chars)
MAX_TEXT_LENGTH = 30000

# Max tokens per response
MAX_TOKENS = 4096

MAX_ARTICLES = 2000
START_FROM = 1 # Reset to 1, since the smart filter handles skipping automatically


# =============================================================================
# JSON SCHEMA FOR RESPONSE FORMAT (OpenAI-compatible, minimized)
# =============================================================================

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "batch_news_analysis",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "sentiment": {
                                "type": "string",
                                "enum": ["Positive", "Negative", "Neutral", "Mixed"]
                            },
                            "sentiment_score": {
                                "type": "number",
                                "description": "-1.0 very negative to 1.0 very positive"
                            },
                            "confidence": {
                                "type": "number",
                                "description": "0.0 to 1.0"
                            },
                            "primary_emotion": {
                                "type": "string",
                                "description": "anger, joy, fear, sadness, surprise, disgust, neutral, hope, anxiety"
                            },
                            "entities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "type": {
                                            "type": "string",
                                            "enum": ["PERSON", "ORGANIZATION", "LOCATION", "EVENT", "PRODUCT", "WORK_OF_ART", "LAW", "DATE", "OTHER"]
                                        },
                                        "context": {"type": "string", "description": "3-5 words"},
                                        "relevance": {
                                            "type": "string",
                                            "enum": ["primary", "secondary", "mentioned"]
                                        }
                                    },
                                    "required": ["name", "type", "context", "relevance"],
                                    "additionalProperties": False
                                },
                                "maxItems": 8,
                                "description": "Max 8 most important entities from title and text"
                            },
                            "concepts": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "concept": {"type": "string"},
                                        "category": {"type": "string"},
                                        "salience": {"type": "number", "description": "0.0 to 1.0"}
                                    },
                                    "required": ["concept", "category", "salience"],
                                    "additionalProperties": False
                                },
                                "maxItems": 5,
                                "description": "Max 5 main concepts"
                            }
                        },
                        "required": ["sentiment", "sentiment_score", "confidence", "primary_emotion", "entities", "concepts"],
                        "additionalProperties": False
                    },
                    "description": "Array of analysis results, one per article in the batch"
                }
            },
            "required": ["results"],
            "additionalProperties": False
        }
    }
}


# =============================================================================
# PROMPT (batched version)
# =============================================================================

BATCH_PROMPT = """You are a media analyst. Analyze the following {batch_size} Russian news articles.
For each article, extract sentiment, entities, and concepts.

IMPORTANT: Return EXACTLY {batch_size} results in the "results" array, in the same order as the articles below.

ARTICLES:
{articles}

Return JSON with a "results" array containing {batch_size} objects. Each object must have:
- sentiment: Positive/Negative/Neutral/Mixed
- sentiment_score: float -1.0 to 1.0
- confidence: float 0.0 to 1.0
- primary_emotion: anger, joy, fear, sadness, surprise, disgust, neutral, hope, anxiety
- entities: array of max 8 objects with name, type (PERSON/ORGANIZATION/LOCATION/EVENT/PRODUCT/WORK_OF_ART/LAW/DATE/OTHER), context (3-5 words), relevance (primary/secondary/mentioned)
- concepts: array of max 5 objects with concept, category, salience (0.0-1.0)"""


def format_article_for_prompt(idx: int, title: str, text: str) -> str:
    """Format a single article for the batch prompt."""
    full = text if text else title
    if len(full) > MAX_TEXT_LENGTH:
        full = full[:MAX_TEXT_LENGTH] + "..."
    return f"""
--- ARTICLE {idx} ---
TITLE: {title}
TEXT: {full}
"""


# =============================================================================
# OPENAI CLIENT (Polza AI compatible)
# =============================================================================

def get_client() -> OpenAI:
    api_key = os.environ.get("POLZA_AI_API_KEY")
    if not api_key:
        raise ValueError(
            "POLZA_AI_API_KEY environment variable not set. "
            "Get your key from Polza AI dashboard."
        )
    return OpenAI(api_key=api_key, base_url=API_BASE)


# =============================================================================
# BATCH ANALYSIS
# =============================================================================

def analyze_batch(articles_batch: List[dict], client: OpenAI) -> List[Optional[dict]]:
    """Send a batch of articles to Polza AI and get structured analysis."""

    batch_size = len(articles_batch)
    articles_text = ""
    for i, article in enumerate(articles_batch, 1):
        title = article.get("Title", "")
        text = article.get("Text", "")
        articles_text += format_article_for_prompt(i, title, text)

    prompt = BATCH_PROMPT.format(batch_size=batch_size, articles=articles_text)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.05,
            max_tokens=MAX_TOKENS,
            response_format=RESPONSE_FORMAT,
        )

        content = response.choices[0].message.content
        result = json.loads(content)
        results = result.get("results", [])

        # Pad with None if we got fewer results than expected
        while len(results) < batch_size:
            results.append(None)
        return results[:batch_size]

    except Exception as e:
        print(f"  ⚠️  Batch API error: {type(e).__name__}: {e}")
        return [None] * batch_size

# =============================================================================
# SMART FILTER
# =============================================================================

def needs_enrichment(article: dict) -> bool:
    """Check if the article is missing sentiment, entities, or concepts."""
    # 1. Missing sentiment score
    if article.get("sentiment_score") is None:
        return True
        
    # 2. Missing entities key completely
    if "entities" not in article:
        return True
        
    # 3. Missing concepts key completely
    if "concepts" not in article:
        return True
        
    return False

# =============================================================================
# MAIN PIPELINE
# =============================================================================

def process_articles(input_path: str, output_path: str):
    print(f"📂 Loading articles from: {input_path}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {input_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)

    if not isinstance(articles, list):
        print("❌ Expected JSON array of articles")
        sys.exit(1)

    articles = articles[:MAX_ARTICLES]
    total_loaded = len(articles)
    
    # Run the smart filter to get indices of articles that actually need processing
    indices_to_process = [i for i, a in enumerate(articles) if needs_enrichment(a)]
    total_to_process = len(indices_to_process)

    print(f"📊 Loaded {total_loaded} articles.")
    print(f"⏭️  Skipping {total_loaded - total_to_process} already-enriched articles.")
    print(f"🚀 Processing {total_to_process} missing/incomplete articles.")
    
    if total_to_process == 0:
        print("✅ Everything is already enriched! Exiting.")
        return

    print(f"🤖 Model: {MODEL_NAME} (batch size: {BATCH_SIZE})")
    client = get_client()

    successful = 0
    failed = 0
    api_calls = 0

    # Process in batches using the filtered indices
    for batch_start in range(0, total_to_process, BATCH_SIZE):

        batch_end = min(batch_start + BATCH_SIZE, total_to_process)
        current_batch_indices = indices_to_process[batch_start:batch_end]
        
        # Extract the actual article dictionaries for this batch
        batch = [articles[i] for i in current_batch_indices]
        
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (total_to_process + BATCH_SIZE - 1) // BATCH_SIZE
        
        if batch_num < START_FROM:
            continue

        print(f"\n[Batch {batch_num}/{total_batches}] Processing queue items {batch_start+1}-{batch_end}")

        results = analyze_batch(batch, client)
        api_calls += 1

        # Save results back to the original articles list using the exact original index
        for i, (original_idx, result) in enumerate(zip(current_batch_indices, results)):
            article = articles[original_idx]
            title = article.get("Title", "")
            print(f"  [Original ID: {original_idx+1}] {title[:50]}{'...' if len(title) > 50 else ''}", end="")

            if result:
                article["sentiment"] = result.get("sentiment")
                article["sentiment_score"] = result.get("sentiment_score")
                article["sentiment_confidence"] = result.get("confidence")
                article["primary_emotion"] = result.get("primary_emotion")
                article["entities"] = result.get("entities", [])
                article["concepts"] = result.get("concepts", [])
                article["analyzed_at"] = datetime.utcnow().isoformat() + "Z"

                ent_count = len(article["entities"])
                conc_count = len(article["concepts"])
                print(f" → {result.get('sentiment')} | {ent_count}E {conc_count}C")
                successful += 1
            else:
                _add_empty_fields(article)
                print(f" → FAILED")
                failed += 1
                
        # Save the ENTIRE articles list (including the ones we skipped)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

        if batch_end < total_to_process:
            time.sleep(DELAY_BETWEEN_CALLS)

    # Save Final
    print(f"\n{'='*60}")
    print(f"📈 Session Results: {successful} OK, {failed} failed.")
    print(f"🔢 API calls made: {api_calls} (vs {total_to_process} individual calls)")
    print(f"💾 Saving full dataset to: {output_path}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print("✅ Done!")


def _add_empty_fields(article: dict):
    """Add null/empty fields when analysis fails."""
    article["sentiment"] = None
    article["sentiment_score"] = None
    article["sentiment_confidence"] = None
    article["primary_emotion"] = None
    article["entities"] = []
    article["concepts"] = []
    article["analyzed_at"] = None


# =============================================================================
# SUMMARY REPORT
# =============================================================================

def print_summary(json_path: str):
    with open(json_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    sentiments = {}
    entity_types = {}
    concept_cats = {}
    total_entities = 0
    total_concepts = 0

    for a in articles:
        s = a.get("sentiment")
        if s:
            sentiments[s] = sentiments.get(s, 0) + 1

        for e in a.get("entities", []):
            total_entities += 1
            t = e.get("type", "UNKNOWN")
            entity_types[t] = entity_types.get(t, 0) + 1

        for c in a.get("concepts", []):
            total_concepts += 1
            cat = c.get("category", "unknown")
            concept_cats[cat] = concept_cats.get(cat, 0) + 1

    print(f"\n{'='*60}")
    print("📊 FULL DATASET ENRICHMENT SUMMARY")
    print(f"{'='*60}")

    print("\nSentiment distribution:")
    for s, c in sorted(sentiments.items()):
        print(f"  {s:10s}: {c} articles")

    print(f"\nEntities extracted: {total_entities} total")
    for t, c in sorted(entity_types.items(), key=lambda x: -x[1]):
        print(f"  {t:15s}: {c}")

    print(f"\nConcept categories: {total_concepts} total")
    for cat, c in sorted(concept_cats.items(), key=lambda x: -x[1]):
        print(f"  {cat:15s}: {c}")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    process_articles(INPUT_FILE, OUTPUT_FILE)
    print_summary(OUTPUT_FILE)