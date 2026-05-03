TOOL_REGISTRY = {}

class register_tool:
    def __init__(self,name,description="",args=None):
        self.name = name
        self.description = description
        if args is None:
            args = []
        self.args = args

    def __call__(self, func):
        TOOL_REGISTRY[self.name] = {
            "name": self.name,
            "description": self.description,
            "args": self.args,
            "function": func,
            "docstring": func.__doc__}
        return func

def get_tool(name):
    """
    Retrieve a registered tool by name.
    """
    return TOOL_REGISTRY[name]


def list_tools():
    """
    Return all registered tools.
    """
    return TOOL_REGISTRY