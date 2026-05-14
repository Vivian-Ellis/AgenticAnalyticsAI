PLANNER_REGISTRY = {}

class register_planner_tool:
    def __init__(self, name, description="", input_schema=None, output_type=None):
        self.name = name
        self.description = description
        self.input_schema = input_schema or {}
        self.output_type = output_type

    def __call__(self, func):
        PLANNER_REGISTRY[self.name] = {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_type": self.output_type,
            "function": func,
            "docstring": func.__doc__}
        return func
    
def get_planner_tool(name):
    """
    Retrieve a registered planner tool by name.
    """
    try:
        return PLANNER_REGISTRY[name]
    except:
        return NotImplementedError

def list_planner_tools():
    """
    Return all registered tools for the planner state.
    """
    return PLANNER_REGISTRY