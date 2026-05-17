from foundry_local_sdk import Configuration, FoundryLocalManager
import json, re, sys


def run():
    Configuration(app_name="SolVS")
    FoundryLocalManager.initialize(Configuration(app_name="SolVS"))
    mgr = FoundryLocalManager.instance

    model_id = "qwen3.5-2b"
    model = mgr.catalog.get_model(model_id)
    if not model:
        print("Model not found in catalog:", model_id)
        return

    # Download if needed
    if not model.is_cached:
        print("Downloading model (may take a while)...")
        try:
            model.download(lambda p: sys.stdout.write(f"\r{p:.1f}%") or sys.stdout.flush())
            print()
        except Exception as e:
            print("Download failed:", e)

    # Load model
    if not model.is_loaded:
        print("Loading model...")
        model.load()

    client = model.get_chat_client()
    # Enforce short deterministic JSON output
    client.settings.max_tokens = 80
    client.settings.temperature = 0
    client.settings.response_format = {"type": "json_object"}

    prompts = [
        "What is the capital of France?",
        "Define the golden ratio.",
        "Translate 'hello' to Spanish.",
        "What is 2+2?",
        "What is the chemical formula for water?",
        "Who wrote 'Pride and Prejudice'?",
    ]

    for p in prompts:
        print("\nPrompt:", p)
        messages = [
            {"role": "system", "content": "You MUST output only a single JSON object with one key \"answer\" whose value is a single short sentence. Do not include any explanations or internal thoughts."},
            {"role": "user", "content": p},
        ]
        try:
            resp = client.complete_chat(messages)
            try:
                text = resp.choices[0].message.content
            except Exception:
                text = str(resp)
            print("Raw response:", text)

            m = re.search(r"\{.*\}", text, re.S)
            if m:
                try:
                    obj = json.loads(m.group(0))
                    print("Parsed answer:", obj.get("answer"))
                except Exception as e:
                    print("JSON parse failed:", e)
            else:
                print("No JSON object found in response")
        except Exception as e:
            print("Completion failed:", e)

    try:
        model.unload()
    except Exception:
        pass


if __name__ == "__main__":
    run()
