from foundry_local_sdk import Configuration, FoundryLocalManager


def main():
    # Initialize the Foundry Local SDK
    config = Configuration(app_name="foundry_local_samples")
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance

    # Download and register all execution providers.
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

    # Select and load a model from the catalog
    model = manager.catalog.get_model("qwen3.5-4b")
    model.download(
        lambda progress: print(
            f"\rDownloading model: {progress:.2f}%",
            end="",
            flush=True,
        )
    )
    print()
    model.load()
    print("Model loaded and ready.")

    # Get a chat client
    client = model.get_chat_client()

    # Create the conversation messages with a strict system prompt to avoid
    # chain-of-thought. The model may still produce reasoning; we post-process
    # to strip internal deliberation.
    messages = [
        {
            "role": "system",
            "content": (
                "You are a concise assistant. Do NOT reveal chain-of-thought, internal "
                "deliberation, or reasoning. Provide only the final answer, in one "
                "short sentence. If the model attempts to show thoughts, omit them "
                "and output only the final answer."
            ),
        },
        {"role": "user", "content": "What is the golden ratio?"},
    ]

    # Use non-streaming completion to avoid long streaming output and cancellations.
    print("Assistant (non-stream):", flush=True)
    full_text = ""
    try:
        try:
            resp = client.complete_chat(messages)
        except TypeError:
            resp = client.complete_chat(messages=messages)
        try:
            full_text = resp.choices[0].message.content
        except Exception:
            full_text = str(resp)
        print(full_text)
    except Exception as e:
        print("Non-streaming call failed:", e)

    # Post-process to remove common chain-of-thought blocks like 'Thinking Process'
    import re

    clean = re.sub(r"(?is)Thinking Process:.*?(?:</think>)", "", full_text)
    clean = re.sub(r"(?is)<think>.*?</think>", "", clean)
    clean = clean.strip()
    if clean:
        lines = [l.strip() for l in clean.splitlines() if l.strip()]
        final = lines[-1]
        print("Final answer (extracted):", final)
    else:
        print("Final answer (extracted): <no content>")

    # Clean up
    model.unload()
    print("Model unloaded.")


if __name__ == "__main__":
    main()
