from foundry_local_sdk import Configuration, FoundryLocalManager


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




    model = manager.catalog.get_model("qwen2.5-0.5b")

    model.download(

        lambda progress: print(

            f"\rDownloading model: {progress:.2f}%", end="", flush=True

        )

    )

    print()

    model.load()

    print("Model loaded and ready.")



    client = model.get_chat_client()




    messages = [

        {

            "role": "system",

            "content": "You are a helpful, friendly assistant. Keep your responses "

            "concise and conversational. If you don't know something, say so.",

        }

    ]


    print("\nChat assistant ready! Type 'quit' to exit.\n")


    while True:

        user_input = input("You: ")

        if user_input.strip().lower() in ("quit", "exit"):

            break



        messages.append({"role": "user", "content": user_input})


  

        print("Assistant: ", end="", flush=True)

        full_response = ""

        for chunk in client.complete_streaming_chat(messages):

            if not chunk.choices:

                continue

            content = chunk.choices[0].delta.content

            if content:

                print(content, end="", flush=True)

                full_response += content

        print("\n")


     

        messages.append({"role": "assistant", "content": full_response})


  

    model.unload()

    print("Model unloaded. Goodbye!")



if __name__ == "__main__":

    main()
