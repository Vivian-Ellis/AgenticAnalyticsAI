COMPARISON_TOOL_REGISTRY = {}

class register_comparison:
    def __init__(self,name, description="",input_schema=None,output_type=None,default_chart=None):
        self.name = name
        self.description = description
        self.input_schema = input_schema or {}
        self.output_type = output_type
        self.default_chart = default_chart

    def __call__(self, func):
        COMPARISON_TOOL_REGISTRY[self.name] = {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_type": self.output_type,
            "default_chart": self.default_chart,
            "function": func,
            "docstring": func.__doc__}
        return func

def get_comparison_tool(name):
    """
    Retrieve a registered comparison tool by name.
    """
    try:
        return COMPARISON_TOOL_REGISTRY[name]
    except:
        print(f"Comparison tool '{name}' is not registered. ")
        print(f"Available tools: {list(COMPARISON_TOOL_REGISTRY.keys())}")
        return NotImplementedError

def list_comparison_tools():
    """
    Return all registered comparison tools.
    """
    return COMPARISON_TOOL_REGISTRY

def list_anthropic_comparison_tools():
    """
    Return all registered tools for the converstation state in a format that can be used by anthropics API tool call.
    """
    anthropic_tools = []
    for tool in COMPARISON_TOOL_REGISTRY.values():
        anthropic_tools.append({
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["input_schema"]
        })

    return anthropic_tools