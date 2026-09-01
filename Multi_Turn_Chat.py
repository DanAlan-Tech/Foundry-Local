import sys
from foundry_local_sdk import Configuration, FoundryLocalManager

def main():
    # Defensive runtime initialization wrap
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

    # Pull system Execution Providers safely
    manager.download_and_register_eps(progress_callback=ep_progress)
    if current_ep:
        print()

    # Load local model weights safely
    model_id = "qwen2.5-0.5b"
    print(f"Resolving model pipeline for: {model_id}")
    model = manager.catalog.get_model(model_id)
    
    model.download(
        lambda progress: print(
            f"\rDownloading model: {progress:.2f}%", end="", flush=True
        )
    )
    print()
    
    model.load()
    print("Model loaded and ready locally.")

    client = model.get_chat_client()

    # Base operating guidelines for the system role
    system_instruction = {
        "role": "system",
        "content": "You are a helpful, friendly assistant. Keep your responses concise and conversational. If you don't know something, say so.",
    }
    
    # SECURITY NOTE: Maintain a strict history window limit to prevent Out-Of-Memory (OOM) state vectors
    MAX_HISTORY_TURNS = 10
    user_conversation_history = []

    print("\nChat assistant ready! Type 'quit' or 'exit' to end the session.\n")

    try:
        while True:
            user_input = input("You: ")
            if user_input.strip().lower() in ("quit", "exit"):
                break

            if not user_input.strip():
                continue

            user_conversation_history.append({"role": "user", "content": user_input})

            # Assemble runtime payload safely balancing global system prompt + capped context slice
            active_payload = [system_instruction] + user_conversation_history[-MAX_HISTORY_TURNS:]

            print("Assistant: ", end="", flush=True)
            full_response = ""
            
            for chunk in client.complete_streaming_chat(active_payload):
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content
                if content:
                    print(content, end="", flush=True)
                    full_response += content
            print("\n")

            user_conversation_history.append({"role": "assistant", "content": full_response})

    except KeyboardInterrupt:
        # Prevent dirty stack traces from throwing when users issue an abrupt Ctrl+C escape
        print("\nSession interrupted via system sequence.")
        
    finally:
        # Enforce explicit memory de-allocation even if runtime exceptions disrupt processing
        print("Cleaning system contexts...")
        model.unload()
        print("Model unloaded. Goodbye!")

if __name__ == "__main__":
    main()

