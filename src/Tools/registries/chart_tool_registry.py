CHART_REGISTRY = {}

class register_chart:
    def __init__(self, name, description="", input_schema=None, output_type=None):
        self.name = name
        self.description = description
        self.input_schema = input_schema or {}
        self.output_type = output_type

    def __call__(self, func):
        CHART_REGISTRY[self.name] = {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_type": self.output_type,
            "function": func,
            "docstring": func.__doc__}
        return func
    
def get_chart_tool(name):
    """
    Retrieve a registered tool by name.
    """
    try:
        return CHART_REGISTRY[name]
    except:
        return NotImplementedError

def list_chart_tools():
    """
    Return all registered tools.
    """
    return CHART_REGISTRY