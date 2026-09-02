"""
Navi-G8 Clarity Index – ChromaDB-backed semantic retrieval.

Provides vector embeddings for nodes, enabling retrieval by meaning
rather than just ID or type. Used by the Orchestrator to find relevant
context before calling the LLM.
"""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from .models import Clarification, FalseProblemFlag, Node, Perturbation, Session, Stream, Trajectory

# ─── Embedding Function ────────────────────────────────────────────────


def get_embedding_function(use_local: bool = True):
    """
    Returns an embedding function for ChromaDB.

    Args:
        use_local: If True, uses sentence-transformers/all-MiniLM-L6-v2 (local, ~80MB).
                   If False, uses the built-in default (which may use a remote API).
    """
    if use_local:
        try:
            return embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        except Exception as e:
            print(f"⚠️  Local embedding model failed to load: {e}")
            print("   Falling back to default embedding function.")
            return embedding_functions.DefaultEmbeddingFunction()
    else:
        return embedding_functions.DefaultEmbeddingFunction()


# ─── Clarity Index ─────────────────────────────────────────────────────


class ClarityIndex:
    """
    ChromaDB-backed vector index for Navi-G8 nodes.

    Stores embeddings of node descriptions, allowing semantic retrieval
    of relevant context for the Orchestrator.

    Usage:
        index = ClarityIndex("~/.navi-g8/clarity_index")
        index.add_node(trajectory)
        results = index.query("pipeline view not rendering", n_results=5)
    """

    def __init__(
        self,
        persist_dir: Union[str, Path],
        use_local_embedding: bool = True,
        collection_name: str = "navi_nodes",
    ):
        self.persist_dir = Path(persist_dir).expanduser().resolve()
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir), settings=Settings(anonymized_telemetry=False)
        )

        # Get embedding function
        self.embed_fn = get_embedding_function(use_local=use_local_embedding)

        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
        except ValueError:
            self.collection = self.client.create_collection(
                name=collection_name, embedding_function=self.embed_fn
            )

        self.collection_name = collection_name

    # ─── Node Text Representation ─────────────────────────────────────

    def _node_to_text(self, node: Node) -> str:
        """Convert a node to a text representation for embedding."""
        if isinstance(node, Trajectory):
            return f"Trajectory: {node.description}. Direction: {node.bearing}. Status: {node.status.value}."
        elif isinstance(node, Stream):
            return f"Stream: {node.path}. Signature: {node.signature or 'unknown'}. Volatility: {node.volatility:.2f}."
        elif isinstance(node, Perturbation):
            return f"Perturbation: {node.description}. Severity: {node.severity}. Frequency: {node.frequency}."
        elif isinstance(node, Clarification):
            return f"Clarification: {node.description}. Rationale: {node.rationale}."
        elif isinstance(node, FalseProblemFlag):
            return f"False Problem Flag: {node.description}. Context: {node.context}."
        elif isinstance(node, Session):
            return f"Session started at {node.started_at}. Coherence history: {node.coherence_history}."
        else:
            return f"Node {node.id} of type {node.type.value}."

    def _node_to_metadata(self, node: Node) -> Dict[str, Any]:
        """Extract metadata from a node for ChromaDB storage."""
        meta = {
            "id": node.id,
            "type": node.type.value,
            "created_at": node.created_at.isoformat(),
        }
        if isinstance(node, Trajectory):
            meta["description"] = node.description
            meta["bearing"] = node.bearing
            meta["status"] = node.status.value
        elif isinstance(node, Stream):
            meta["path"] = node.path
            meta["volatility"] = node.volatility
        elif isinstance(node, Perturbation):
            meta["description"] = node.description
            meta["severity"] = node.severity
            meta["resolved"] = node.resolved
        elif isinstance(node, Clarification):
            meta["description"] = node.description
        elif isinstance(node, FalseProblemFlag):
            meta["description"] = node.description
            meta["context"] = node.context
            meta["resolved"] = node.resolved
        return meta

    # ─── CRUD Operations ──────────────────────────────────────────────

    def add_node(self, node: Node) -> None:
        """
        Add a node to the clarity index.

        If a node with the same ID already exists, it will be updated.
        """
        text = self._node_to_text(node)
        metadata = self._node_to_metadata(node)

        # Check if node already exists
        existing = self.collection.get(ids=[node.id])
        if existing["ids"]:
            # Update
            self.collection.update(ids=[node.id], documents=[text], metadatas=[metadata])
        else:
            # Add
            self.collection.add(ids=[node.id], documents=[text], metadatas=[metadata])

    def add_nodes(self, nodes: List[Node]) -> None:
        """Add multiple nodes to the clarity index."""
        for node in nodes:
            self.add_node(node)

    def delete_node(self, node_id: str) -> None:
        """Remove a node from the clarity index."""
        self.collection.delete(ids=[node_id])

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a node's embedding data by ID."""
        result = self.collection.get(ids=[node_id])
        if result["ids"]:
            return {
                "id": result["ids"][0],
                "document": result["documents"][0] if result["documents"] else None,
                "metadata": result["metadatas"][0] if result["metadatas"] else None,
                "embedding": result["embeddings"][0] if result["embeddings"] else None,
            }
        return None

    # ─── Query ─────────────────────────────────────────────────────────

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query the clarity index for semantically similar nodes.

        Args:
            query_text: The text to search for.
            n_results: Number of results to return.
            where: Filter by metadata (e.g., {"type": "trajectory"}).
            where_document: Filter by document content.

        Returns:
            List of results, each containing id, document, metadata, and distance.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted = []
        if results["ids"]:
            for i, node_id in enumerate(results["ids"][0]):
                formatted.append(
                    {
                        "id": node_id,
                        "document": results["documents"][0][i] if results["documents"] else None,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else None,
                        "distance": results["distances"][0][i] if results["distances"] else None,
                    }
                )
        return formatted

    def query_by_type(
        self, query_text: str, node_type: str, n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query the clarity index, filtering by node type.

        Args:
            query_text: The text to search for.
            node_type: The node type to filter by (e.g., "trajectory").
            n_results: Number of results to return.
        """
        return self.query(query_text=query_text, n_results=n_results, where={"type": node_type})

    def query_similar_to_node(
        self, node: Node, n_results: int = 5, exclude_self: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query for nodes similar to a given node.

        Args:
            node: The node to use as the query.
            n_results: Number of results to return.
            exclude_self: If True, exclude the node itself from results.
        """
        text = self._node_to_text(node)
        results = self.query(query_text=text, n_results=n_results + (1 if exclude_self else 0))

        if exclude_self:
            results = [r for r in results if r["id"] != node.id]
            results = results[:n_results]

        return results

    # ─── Stats ─────────────────────────────────────────────────────────

    def count(self) -> int:
        """Return the number of nodes in the index."""
        return self.collection.count()

    def list_ids(self) -> List[str]:
        """Return all node IDs in the index."""
        result = self.collection.get()
        return result["ids"] if result["ids"] else []

    def clear(self) -> None:
        """Clear all nodes from the index."""
        ids = self.list_ids()
        if ids:
            self.collection.delete(ids=ids)

    # ─── Persistence ──────────────────────────────────────────────────

    def persist(self) -> None:
        """Persist the index to disk. (ChromaDB does this automatically.)"""
        # ChromaDB persists automatically, but we can force a flush if needed.
        pass

    def close(self) -> None:
        """Close the ChromaDB client."""
        # No explicit close needed for ChromaDB's persistent client
        pass
