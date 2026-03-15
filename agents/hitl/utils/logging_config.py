
import logging
import sys
# from langfuse.decorators import observe, langfuse_context

# 1. Standard Python Logging Setup
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("agent_system.log")
        ]
    )
    # Optional: Enable Langfuse internal debug logs if needed
    # logging.getLogger("langfuse").setLevel(logging.DEBUG)


# # 2. Integrated Agentic Logic
# @observe()  # Automatically starts a Langfuse trace
# def run_agent_step(task_input: str):
#     logger.info(f"Starting agent task: {task_input}")
    
#     try:
#         # Simulate an LLM or Tool call
#         result = "Processed Data" 
        
#         # Log success to Langfuse trace for visibility
#         langfuse_context.update_current_observation(
#             metadata={"status": "success", "input_len": len(task_input)}
#         )
#         return result

#     except Exception as e:
#         # LOG TO SYSTEM: For infrastructure monitoring (Datadog/Sentry)
#         logger.error(f"Critical System Failure: {str(e)}", exc_info=True)
        
#         # LOG TO LANGFUSE: To flag this specific AI run as "Failed" in the UI
#         langfuse_context.update_current_observation(
#             level="ERROR",
#             status_message=f"Agent failed during tool execution: {str(e)}"
#         )
#         raise e

# Initialize on startup
setup_logging()
logger = logging.getLogger("hr_rag_agent")
logger.info("Starting agent task: task_input")
logger.warning("This is a warning message for task_input")




import logging
import sys
from functools import wraps

# 1. Centralized Logger Setup
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("agent_system.log")
        ]
    )

logger = logging.getLogger("AgentSystem")
setup_logging()

# 2. The "Attribute-level" Logging Decorator
def log_task(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Log the start and the input arguments
        logger.info(f"Starting {func.__name__} with input: {args} {kwargs}")
        
        try:
            result = func(*args, **kwargs)
            # Log successful completion
            logger.info(f"Completed {func.__name__} successfully.")
            return result
            
        except Exception as e:
            # Centralized Error Logging
            logger.error(f"Critical Failure in {func.__name__}: {str(e)}", exc_info=True)
            raise e
            
    return wrapper
 
# 3. Clean Implementation
@log_task
def run_agent_step(task_input: str):
    # Business logic is now separate from logging boilerplate
    result = f"Processed: {task_input}"
    return result

# Execution
if __name__ == "__main__":
    run_agent_step("Example task input for the agent")


############## Class level logging decorator example ##############
def log_all_methods(cls):
    for attr_name, attr_value in cls.__dict__.items():
        # Only decorate callables that aren't "magic" dunder methods
        if callable(attr_value) and not attr_name.startswith("__"):
            setattr(cls, attr_name, log_task(attr_value))
    return cls

@log_all_methods
class Agent:
    def step_one(self, data):
        return f"Step 1: {data}"

    def step_two(self, data):
        return f"Step 2: {data}"
############## Class level logging decorator example ##############

############## Module level logging decorator example ##############
import sys
import types

def apply_module_logging():
    # Get the current module object
    module = sys.modules[__name__]
    for attr_name in dir(module):
        attr_value = getattr(module, attr_name)
        # Check if it's a function defined in THIS module
        if isinstance(attr_value, types.FunctionType) and attr_value.__module__ == __name__:
            if attr_name != "log_task": # Don't decorate the decorator itself
                setattr(module, attr_name, log_task(attr_value))

# --- Define your functions here ---
def task_a(): pass
def task_b(): pass

# Call this at the very end of the file
apply_module_logging()

############## Module level logging decorator example ##############
