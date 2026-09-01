import json
import ast
import operator
from foundry_local_sdk import Configuration, FoundryLocalManager


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city or location",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit",
                    },
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform a math calculation safely without eval",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The simple math expression to evaluate (e.g., '2 + 2')",
                    }
                },
                "required": ["expression"],
            },
        },
    },
]

def get_weather(location, unit="celsius"):
    """Simulate a weather lookup."""
    return {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "condition": "Sunny",
    }

def safe_eval_math(expr):
    """Safely parse and evaluate simple mathematical text without using eval()."""
 
    operators = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.USub: operator.neg, ast.UAdd: operator.pos
    }
    
    def _eval(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](_eval(node.operand))
        else:
            raise TypeError(f"Unsupported mathematical expression element: {type(node)}")

    try:
    
        tree = ast.parse(expr, mode='eval')
        return _eval(tree.body)
    except Exception as e:
        return f"Error parsing expression safely: {str(e)}"

def calculate(expression):
    """Evaluate a math expression via non-executable secure AST parsing."""
    allowed = set("0123456789+-*/(). ")
    if not all(c in allowed for c in expression):
        return {"error": "Invalid characters detected in mathematical expression"}
        
    result = safe_eval_math(expression)
    if isinstance(result, str) and result.startswith("Error"):
        return {"error": result}
    return {"expression": expression, "result": result}

tool_functions = {"get_weather": get_weather, "calculate": calculate}

def process_tool_calls(messages, response, client):
    """Handle tool calls in a loop until the model produces a final answer."""
    if not response or not response.choices:
        return "Error: Empty tool response from local model tracking client."
        
    choice = response.choices[0].message

    while getattr(choice, 'tool_calls', None):
        assistant_msg = {
            "role": "assistant",
            "content": getattr(choice, 'content', ''),
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in choice.tool_calls
            ],
        }
        messages.append(assistant_msg)

        for tool_call in choice.tool_calls:
            function_name = tool_call.function.name
            
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}

            print(f"  Tool execution routing: {function_name}({arguments})")

            func = tool_functions.get(function_name)
            if func:
                try:
                    result = func(**arguments)
                except Exception as e:
                    result = {"error": f"Internal execution failure on target logic: {str(e)}"}
            else:
                result = {"error": f"Function entry target '{function_name}' was not found in catalog setup."}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

        response = client.complete_chat(messages, tools=tools)
        if not response or not response.choices:
            return "Error: Sequential connection dropped during execution routing loop."
        choice = response.choices[0].message

    return getattr(choice, 'content', 'No descriptive output generated.')

def main():
    config = Configuration(app_name="foundry_local_samples")
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance

    current_ep = ""

    def ep_progress(ep_name: str, percent: float):
        nonlocal current_ep
        if ep_name != current_ep:
            if current_ep:
                print()
            current_ep = ep_name
        print(f"\r  {ep_name:<30}  {percent:5.1f}%", end="", flush=True)

    manager.download_and_register_eps(progress_callback=ep_progress)
    if current_ep:
        print()

    model_id = "qwen2.5-0.5b"
    model = manager.catalog.get_model(model_id)
    model.download(
        lambda progress: print(
            f"\rDownloading model pipeline assets: {progress:.2f}%", end="", flush=True
        )
    )
    print()
    model.load()
    print(f"Model [{model_id}] loaded and ready offline.")

    client = model.get_chat_client()

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant with access to tools. Use them when needed to answer questions accurately.",
        }
    ]

    print("\nTool-calling assistant ready! Type 'quit' or 'exit' to escape execution window.\n")

  
    MAX_ROUNDS_CAP = 15

    try:
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("quit", "exit"):
                break
                
            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})
            
    
            if len(messages) > MAX_ROUNDS_CAP:
                messages = [messages[0]] + messages[-MAX_ROUNDS_CAP:]

            response = client.complete_chat(messages, tools=tools)
            answer = process_tool_calls(messages, response, client)

            messages.append({"role": "assistant", "content": answer})
            print(f"Assistant: {answer}\n")

    except KeyboardInterrupt:
        print("\nSession stopped via termination command.")
    finally:
        print("De-allocating operational memory blocks...")
        model.unload()
        print("Model unloaded. Goodbye!")

if __name__ == "__main__":
    main()
