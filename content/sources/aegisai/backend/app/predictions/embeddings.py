"""Graph embeddings via Neo4j GDS (Phase 16.1).

Computes FastRP (default, deterministic with a seed) or Node2Vec node embeddings
and writes them to the `embedding` node property in Neo4j (so they are stored and
reusable). Returns the embeddings keyed by (label, entity_id) for link prediction.
"""

import logging

from backend.app.graph.analytics import _KEY
from backend.app.graph.neo4j_client import get_client

log = logging.getLogger("predictions.embeddings")

GRAPH_NAME = "cti_embeddings"
DIMENSION = 64
SEED = 42


def _project(client):
    client.run_write("CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName", {"g": GRAPH_NAME})
    client.run_write(
        "CALL gds.graph.project($g, '*', {REL: {type: '*', orientation: 'UNDIRECTED'}}) "
        "YIELD graphName RETURN graphName", {"g": GRAPH_NAME})


def compute_embeddings(model: str = "fastrp", dimension: int = DIMENSION) -> int:
    """Compute + persist node embeddings. Returns nodes written."""
    client = get_client()
    _project(client)
    if model == "node2vec":
        cypher = ("CALL gds.node2vec.write($g, {embeddingDimension:$d, randomSeed:$s, "
                  "writeProperty:'embedding'}) YIELD nodePropertiesWritten RETURN nodePropertiesWritten")
    else:
        cypher = ("CALL gds.fastRP.write($g, {embeddingDimension:$d, randomSeed:$s, "
                  "writeProperty:'embedding'}) YIELD nodePropertiesWritten RETURN nodePropertiesWritten")
    # GDS *.write is a write procedure -> must run in a write transaction.
    client.run_write(cypher, {"g": GRAPH_NAME, "d": dimension, "s": SEED})
    client.run_write("CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName", {"g": GRAPH_NAME})
    rows = client.run_read("MATCH (n) WHERE n.embedding IS NOT NULL RETURN count(n) AS n")
    written = rows[0]["n"] if rows else 0
    log.info("Embeddings written: %s (%s, dim=%s)", written, model, dimension)
    return written


def load_embeddings(labels: set[str] | None = None) -> dict:
    """Read persisted embeddings as {(label, entity_id): vector}."""
    client = get_client()
    rows = client.run_read(
        "MATCH (n) WHERE n.embedding IS NOT NULL "
        f"RETURN labels(n)[0] AS label, {_KEY} AS entity_id, n.embedding AS emb"
    )
    out = {}
    for r in rows:
        if labels and r["label"] not in labels:
            continue
        if r["entity_id"] is not None:
            out[(r["label"], r["entity_id"])] = r["emb"]
    return out
