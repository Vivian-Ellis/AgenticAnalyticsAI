ANALYTICS_TOOL_REGISTRY = {}

class register_analytics_tool:
    def __init__(self,name, description="",input_schema=None,output_type=None,default_chart=None):
        self.name = name
        self.description = description
        self.input_schema = input_schema or {}
        self.output_type = output_type
        self.default_chart = default_chart

    def __call__(self, func):
        ANALYTICS_TOOL_REGISTRY[self.name] = {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_type": self.output_type,
            "default_chart": self.default_chart,
            "function": func,
            "docstring": func.__doc__}
        return func

def get_tool(name):
    """
    Retrieve a registered tool by name.
    """
    try:
        return ANALYTICS_TOOL_REGISTRY[name]
    except:
        print(f"Analytics tool '{name}' is not registered. ")
        print(f"Available tools: {list(ANALYTICS_TOOL_REGISTRY.keys())}")
        return NotImplementedError

def list_tools():
    """
    Return all registered tools.
    """
    return ANALYTICS_TOOL_REGISTRY