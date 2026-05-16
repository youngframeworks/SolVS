from foundry_local_sdk import Configuration, FoundryLocalManager
import json, re, sys, time


def ensure_model(model_id="qwen3.5-2b"):
    Configuration(app_name="SolVS")
    FoundryLocalManager.initialize(Configuration(app_name="SolVS"))
    mgr = FoundryLocalManager.instance
    model = mgr.catalog.get_model(model_id)
    if not model:
        print("Model not found in catalog:", model_id)
        return None
    if not model.is_cached:
        print("Downloading model (may take a while)...")
        try:
            model.download(lambda p: sys.stdout.write(f"\r{p:.1f}%") or sys.stdout.flush())
            print()
        except Exception as e:
            print("Download failed:", e)
    if not model.is_loaded:
        print("Loading model...")
        model.load()
    return model


def extract_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def try_prompt(client, prompt, strong=False):
    # strong: use more forceful system prompt
    system = (
        "You MUST output only a single JSON object with one key \"answer\" whose value is a single short sentence."
        " Do not include any explanations or internal thoughts. Output exactly the JSON object and nothing else."
    ) if strong else (
        "You MUST output only a single JSON object with one key \"answer\" whose value is a single short sentence. Do not include any explanations or internal thoughts."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    try:
        resp = client.complete_chat(messages)
        try:
            text = resp.choices[0].message.content
        except Exception:
            text = str(resp)
        j = extract_json(text)
        return text, j, None
    except Exception as e:
        return None, None, e


def main():
    model = ensure_model()
    if not model:
        return
    client = model.get_chat_client()
    client.settings.max_tokens = 80
    client.settings.temperature = 0
    client.settings.response_format = {"type": "json_object"}

    prompts = [
        "Who wrote 'Pride and Prejudice'?",
        "What is the capital of France?",
        "Define the golden ratio.",
        "Translate 'hello' to Spanish.",
        "What is 2+2?",
        "What is the chemical formula for water?",
        "List three prime numbers under 10.",
        "What year did the moon landing occur?",
        "Name the inventor of the telephone.",
        "Give a one-sentence summary of '1984' by George Orwell.",
        "What is the largest mammal?",
        "Convert 100 Celsius to Fahrenheit.",
        "What is the capital of Japan?",
        "Who painted the Mona Lisa?",
        "What is the boiling point of water in Celsius?",
        "What is the derivative of x^2?",
        "Spell the word 'accommodate'.",
        "What is the currency of Germany?",
        "How many continents are there?",
        "What is the atomic number of carbon?",
        "Who is the author of 'The Odyssey'?",
        "What is the smallest prime number?",
        "Translate 'good night' to French.",
        "What does HTTP stand for?",
        "Name a mammal that lays eggs.",
        "What is the capital of Canada?",
        "What is the square root of 16?",
        "Who discovered penicillin?",
        "What is the speed of light in vacuum (m/s)?",
        "What is the main ingredient in guacamole?",
    ]

    results = []
    for p in prompts:
        print("\nPrompt:", p)
        text, j, err = try_prompt(client, p, strong=False)
        if err:
            print("Attempt failed:", err)
            # try strong
            text, j, err2 = try_prompt(client, p, strong=True)
            if err2:
                print("Strong attempt failed:", err2)
                results.append((p, None, str(err2)))
                continue
            else:
                print("Raw response (strong):", text)
                if j:
                    print("Parsed answer:", j.get("answer"))
                    results.append((p, j.get("answer"), None))
                else:
                    print("No JSON found in strong response")
                    results.append((p, None, "no-json"))
                continue
        # no error
        print("Raw response:", text)
        if j:
            print("Parsed answer:", j.get("answer"))
            results.append((p, j.get("answer"), None))
            continue
        # if no JSON, try strong
        print("No JSON found; retrying with stronger prompt")
        text2, j2, err2 = try_prompt(client, p, strong=True)
        if err2:
            print("Strong attempt failed:", err2)
            results.append((p, None, str(err2)))
            continue
        print("Raw response (strong):", text2)
        if j2:
            print("Parsed answer:", j2.get("answer"))
            results.append((p, j2.get("answer"), None))
        else:
            print("No JSON found in strong response; extracting fallback")
            # fallback: last non-empty line
            lines = [ln.strip() for ln in (text2 or "").splitlines() if ln.strip()]
            fallback = lines[-1] if lines else None
            results.append((p, fallback, "fallback-extracted" if fallback else "no-answer"))

    print("\nSummary:\n")
    for p, ans, err in results:
        print(f"- Prompt: {p}\n  Answer: {ans}\n  Error: {err}\n")

    try:
        model.unload()
    except Exception:
        pass


if __name__ == "__main__":
    main()
