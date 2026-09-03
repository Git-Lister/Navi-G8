"""
Unit tests for the Navi-G8 scaffold (cognitive layer).
"""

import pytest

from navi_agent.scaffold.graph_store import GraphStore
from navi_agent.scaffold.models import (
    Clarification,
    Edge,
    EdgeType,
    FalseProblemFlag,
    NodeType,
    Perturbation,
    Session,
    Stream,
    Trajectory,
    TrajectoryStatus,
)


def test_graph_store_basic(tmp_path):
    """Test basic CRUD operations on nodes and edges."""
    db_path = tmp_path / "test_graph.db"
    store = GraphStore(db_path)
    store.init_db()

    # Create nodes
    t = Trajectory(description="Build pipeline")
    s = Stream(path="src/main.py", volatility=0.3)
    store.add_node(t)
    store.add_node(s)

    # Create edge
    store.add_edge(Edge(source_id=t.id, target_id=s.id, type=EdgeType.DEPENDS_ON))

    # Retrieve nodes directly
    retrieved_t = store.get_node(t.id)
    retrieved_s = store.get_node(s.id)

    assert retrieved_t is not None
    assert retrieved_s is not None
    assert retrieved_t.description == "Build pipeline"
    assert retrieved_s.path == "src/main.py"

    # Query by type – FIXED: use NodeType enum, not class
    trajectories = store.query_nodes(node_type=NodeType.TRAJECTORY)
    streams = store.query_nodes(node_type=NodeType.STREAM)
    assert len(trajectories) == 1
    assert len(streams) == 1


def test_graph_store_with_session(tmp_path):
    """Test that get_field_state returns nodes attached to a session."""
    db_path = tmp_path / "test_session.db"
    store = GraphStore(db_path)
    store.init_db()

    # Create a session
    session = Session()
    store.add_node(session)

    # Create nodes
    t = Trajectory(description="Build pipeline")
    s = Stream(path="src/main.py")
    store.add_node(t)
    store.add_node(s)

    # Link nodes to session
    store.add_edge(Edge(source_id=session.id, target_id=t.id, type=EdgeType.BELONGS_TO))
    store.add_edge(Edge(source_id=session.id, target_id=s.id, type=EdgeType.BELONGS_TO))

    # Get field state
    field = store.get_field_state(session_id=session.id)

    assert len(field.trajectories) == 1
    assert len(field.streams) == 1
    assert field.trajectories[0].description == "Build pipeline"


def test_false_problem_flag(tmp_path):
    """Test creating and resolving a false problem flag."""
    db_path = tmp_path / "test_flags.db"
    store = GraphStore(db_path)
    store.init_db()

    flag = FalseProblemFlag(
        description="Are we sure the processor persists?",
        context="Pipeline view failure",
        resolved=False,
    )
    store.add_node(flag)

    retrieved = store.get_node(flag.id)
    assert isinstance(retrieved, FalseProblemFlag)
    assert retrieved.resolved is False

    # Resolve it
    flag.resolved = True
    flag.resolution_insight = "Processor is stored in module-level variable"
    store.add_node(flag)  # upsert

    retrieved2 = store.get_node(flag.id)
    assert retrieved2.resolved is True
    assert "module-level" in retrieved2.resolution_insight


def test_clarity_index_basic(tmp_path):
    """Test basic add/query operations on the clarity index."""
    from navi_agent.scaffold.clarity_index import ClarityIndex

    index_dir = tmp_path / "clarity_index"
    index = ClarityIndex(index_dir, use_local_embedding=True)

    # Create nodes
    t = Trajectory(description="Build pipeline for OCR extraction")
    s = Stream(path="src/ocr/extract.py", volatility=0.6)
    p = Perturbation(description="Tesseract fails on rotated images", severity="high")

    # Add to index
    index.add_node(t)
    index.add_node(s)
    index.add_node(p)

    # Query
    results = index.query("OCR extraction pipeline", n_results=3)

    assert len(results) >= 1
    # The trajectory should be most relevant
    assert any(r["id"] == t.id for r in results)

    # Query by type
    results_traj = index.query_by_type("pipeline", "trajectory", n_results=5)
    assert all(r["metadata"]["type"] == "trajectory" for r in results_traj)


def test_clarity_index_update(tmp_path):
    """Test that updating a node updates its embedding."""
    from navi_agent.scaffold.clarity_index import ClarityIndex

    index_dir = tmp_path / "clarity_update"
    index = ClarityIndex(index_dir, use_local_embedding=True)

    t = Trajectory(description="Build pipeline", bearing="Initial exploration")
    index.add_node(t)

    # Update the trajectory
    t.bearing = "Focusing on OCR first"
    index.add_node(t)  # Should update

    # Query should reflect the new bearing
    results = index.query("OCR first", n_results=3)
    assert any(r["id"] == t.id for r in results)


def test_clarity_index_similar_to_node(tmp_path):
    """Test querying for nodes similar to a given node."""
    from navi_agent.scaffold.clarity_index import ClarityIndex

    index_dir = tmp_path / "clarity_similar"
    index = ClarityIndex(index_dir, use_local_embedding=True)

    t1 = Trajectory(description="Build OCR extraction pipeline")
    t2 = Trajectory(description="Build LLM parser for family trees")
    s = Stream(path="src/ocr/extract.py")

    index.add_nodes([t1, t2, s])

    # Query similar to t1
    results = index.query_similar_to_node(t1, n_results=2)

    assert len(results) >= 1
    # The most similar should be t2 (both are trajectories about building pipeline

    # ─── Orchestrator Tests ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_orchestrator_basic(tmp_path):
        """Test basic orchestrator flow with a simple query."""
        from navi_agent.gateway import LLMGateway
        from navi_agent.scaffold.orchestrator import FieldOrchestrator

        # Setup
        db_path = tmp_path / "test_orchestrator.db"
        index_dir = tmp_path / "orchestrator_index"

        store = GraphStore(db_path)
        store.init_db()

        index = ClarityIndex(index_dir, use_local_embedding=True)

        # Mock gateway that returns a structured response
        class MockGateway:
            async def generate(self, prompt: str, system: str = None) -> str:
                return """
                INSIGHT: The pipeline view fails because the processor is stored in app.storage.general,
                which cannot hold complex objects. The clarification is to move the processor to a
                module-level variable in state.py.

                ACTION: Move processor to state.py as a module-level variable.

                CONFIDENCE: 0.85
                """

        gateway = MockGateway()

        orch = FieldOrchestrator(store, index, gateway)

        # Process a query
        response = await orch.process("The pipeline view isn't rendering")

        # Check response
        assert response.insight is not None
        assert "processor" in response.insight.lower()
        assert response.confidence == 0.85
        assert response.clarification_id is not None

        # Check that the clarification was added to the graph
        clarification = store.get_node(response.clarification_id)
        assert clarification is not None
        assert isinstance(clarification, Clarification)
        assert "processor" in clarification.rationale.lower()

        # Check that a stream was created
        streams = store.query_nodes(node_type=NodeType.STREAM)
        assert len(streams) == 1
        assert "state.py" in streams[0].path

    @pytest.mark.asyncio
    async def test_orchestrator_debug(tmp_path):
        """Test the debug_perturbation protocol."""
        from navi_agent.scaffold.orchestrator import FieldOrchestrator

        # Setup
        db_path = tmp_path / "test_debug.db"
        index_dir = tmp_path / "debug_index"

        store = GraphStore(db_path)
        store.init_db()

        index = ClarityIndex(index_dir, use_local_embedding=True)

        class MockGateway:
            async def generate(self, prompt: str, system: str = None) -> str:
                return """
                INSIGHT: The UnboundLocalError occurs because the 'processor' variable is assigned
                inside a conditional block but referenced outside it. This is a scoping issue.

                ACTION: Move the processor assignment to the top of the function.

                CONFIDENCE: 0.9
                """

        gateway = MockGateway()
        orch = FieldOrchestrator(store, index, gateway)

        # Process a perturbation
        response = await orch.debug_perturbation(
            error_description="UnboundLocalError: local variable 'processor' referenced before assignment",
            stack_trace="File 'state.py', line 42, in get_processor\n    return processor",
        )

        assert response.insight is not None
        assert "UnboundLocalError" in response.insight or "scoping" in response.insight
        assert response.confidence == 0.9

        # Check that perturbation was created and resolved
        perturbations = store.query_nodes(node_type=NodeType.PERTURBATION)
        assert len(perturbations) == 1
        assert perturbations[0].resolved is True
        assert perturbations[0].resolution_insight is not None
