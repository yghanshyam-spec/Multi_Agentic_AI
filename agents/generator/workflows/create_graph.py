"""
agents/generator/workflows/create_graph.py
============================================
LangGraph graph assembly for the Generator agent.
Node functions live in workflows/nodes/ — one file per node.
"""
from __future__ import annotations

try:
    from langgraph.graph import StateGraph, END
    _LG = True
except ImportError:
    _LG = False


def build_generator_graph():
    """Assemble and compile the Generator LangGraph workflow."""
    if not _LG:
        return None

    from agents.generator.workflows.nodes.select_template_node  import select_template_node
    from agents.generator.workflows.nodes.collect_inputs_node   import collect_inputs_node
    from agents.generator.workflows.nodes.plan_content_node     import plan_content_node
    from agents.generator.workflows.nodes.generate_section_node import generate_section_node
    from agents.generator.workflows.nodes.review_content_node   import review_content_node
    from agents.generator.workflows.nodes.refine_content_node   import refine_content_node
    from agents.generator.workflows.nodes.assemble_document_node import assemble_document_node
    from agents.generator.workflows.edges import should_refine

    g = StateGraph(dict)
    g.add_node("select_template_node",  select_template_node)
    g.add_node("collect_inputs_node",   collect_inputs_node)
    g.add_node("plan_content_node",     plan_content_node)
    g.add_node("generate_section_node", generate_section_node)
    g.add_node("review_content_node",   review_content_node)
    g.add_node("refine_content_node",   refine_content_node)
    g.add_node("assemble_document_node", assemble_document_node)

    g.set_entry_point("select_template_node")
    g.add_edge("select_template_node",  "collect_inputs_node")
    g.add_edge("collect_inputs_node",   "plan_content_node")
    g.add_edge("plan_content_node",     "generate_section_node")
    g.add_edge("generate_section_node", "review_content_node")
    g.add_conditional_edges("review_content_node", should_refine,
        {"refine_content_node": "refine_content_node",
         "assemble_document_node": "assemble_document_node"})
    g.add_edge("refine_content_node",   "assemble_document_node")
    g.add_edge("assemble_document_node", END)

    return g.compile()
