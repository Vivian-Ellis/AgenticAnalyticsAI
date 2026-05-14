CONVERSATION_REGISTRY = {}

class register_conversation:
    def __init__(self, name, description="", input_schema=None, output_type=None):
        self.name = name
        self.description = description
        self.input_schema = input_schema or {}
        self.output_type = output_type

    def __call__(self, func):
        CONVERSATION_REGISTRY[self.name] = {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_type": self.output_type,
            "function": func,
            "docstring": func.__doc__}
        return func
    
def get_conversation_tool(name):
    """
    Retrieve a registered conversation tool by name.
    """
    try:
        return CONVERSATION_REGISTRY[name]
    except:
        return NotImplementedError

def list_conversation_tools():
    """
    Return all registered tools for the conversation state.
    """
    return CONVERSATION_REGISTRY

def list_anthropic_conversation_tools():
    """
    Return all registered tools for the converstation state in a format that can be used by anthropics API tool call.
    """
    anthropic_tools = []
    for tool in CONVERSATION_REGISTRY.values():
        anthropic_tools.append({
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["input_schema"]
        })

    return anthropic_tools