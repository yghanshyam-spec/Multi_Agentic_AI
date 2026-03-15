"""
Streamlit-based UI adapter for human-in-the-loop interaction.

Run with: streamlit run hitl_langgraph/ui_adapters/streamlit_adapter.py
"""
import streamlit as st
from typing import Dict, Any
from agent_hitl.schemas.graph_state import HITLState 
from agent_hitl.utils.logger import get_logger

logger = get_logger("hitl.streamlit")


class StreamlitAdapter:
    """
    Streamlit UI adapter for human-in-the-loop interaction.
    Provides a web-based approval interface.
    """

    def human_node(self, state: HITLState) -> HITLState:
        """
        Displays the agent output and collects approval via Streamlit widgets.
        NOTE: This is designed to be called within a Streamlit app context.
        """
        st.header("🔔 Human Review Required")
        st.markdown(f"**Checkpoint:** `{state.get('checkpoint_name', 'Unknown')}`")
        st.text_area("Agent Output", value=state.get("agent_output", ""), height=200, disabled=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Approve", type="primary"):
                state["approved"] = True
                feedback = st.text_input("Feedback (optional)")
                state["human_feedback"] = feedback if feedback else None
                st.success("Approved!")
                logger.info("Human approved via Streamlit.")

        with col2:
            if st.button("❌ Reject"):
                state["approved"] = False
                feedback = st.text_input("Reason for rejection")
                state["human_feedback"] = feedback if feedback else "Rejected."
                st.error("Rejected.")
                logger.info("Human rejected via Streamlit.")

        return state
