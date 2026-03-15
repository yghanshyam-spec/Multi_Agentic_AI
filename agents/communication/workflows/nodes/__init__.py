"""agents/communication/workflows/nodes — one file per workflow node."""
from agents.communication.workflows.nodes.omnichannel_nodes import (
    detect_channel_node, load_context_node, classify_message_node,
    draft_response_node, check_consistency_node, dispatch_response_node,
    update_context_node,
)
from agents.communication.workflows.nodes.broadcast_nodes import (
    detect_channel_node as broadcast_detect_channel_node,
)

__all__ = [
    "detect_channel_node", "load_context_node", "classify_message_node",
    "draft_response_node", "check_consistency_node", "dispatch_response_node",
    "update_context_node",
]
