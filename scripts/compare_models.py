#!/usr/bin/env python3
from foundry_local_sdk import Configuration, FoundryLocalManager
import json, re, sys, time, csv, os
from datetime import datetime
import argparse


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
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def try_prompt(client, prompt, strong=False):
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
    start = time.time()
    try:
        resp = client.complete_chat(messages)
        elapsed = time.time() - start
        try:
            text = resp.choices[0].message.content
        except Exception:
            text = str(resp)
        j = extract_json(text)
        return text, j, None, elapsed
    except Exception as e:
        return None, None, e, None


def run_trials(model_id, prompts, trials=3, outdir="runtime/reports"):
    model = ensure_model(model_id)
    if not model:
        raise SystemExit(1)
    client = model.get_chat_client()
    client.settings.max_tokens = 120
    client.settings.temperature = 0
    client.settings.response_format = {"type": "json_object"}

    os.makedirs(outdir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    json_path = os.path.join(outdir, f"compare_{model_id}_{timestamp}.json")
    csv_path = os.path.join(outdir, f"compare_{model_id}_{timestamp}.csv")

    records = []
    for t in range(1, trials + 1):
        print(f"\n=== Trial {t}/{trials} for {model_id} ===")
        for p in prompts:
            print("Prompt:", p)
            text, j, err, elapsed = try_prompt(client, p, strong=False)
            fallback = False
            if err:
                print("Attempt failed:", err)
                text, j, err2, elapsed = try_prompt(client, p, strong=True)
                if err2:
                    print("Strong attempt failed:", err2)
                    rec = {"model": model_id, "trial": t, "prompt": p, "raw": None, "answer": None, "success": False, "error": str(err2), "time": None, "fallback": False}
                    records.append(rec)
                    continue
                else:
                    print("Raw response (strong):", text)
            else:
                print("Raw response:", text)
            if j:
                ans = j.get("answer")
                success = True
            else:
                # try strong if not already
                if not err:
                    print("No JSON found; retrying with stronger prompt")
                    text2, j2, err2, elapsed2 = try_prompt(client, p, strong=True)
                    if err2:
                        print("Strong attempt failed:", err2)
                        rec = {"model": model_id, "trial": t, "prompt": p, "raw": text2 or text, "answer": None, "success": False, "error": str(err2), "time": elapsed2 or elapsed, "fallback": False}
                        records.append(rec)
                        continue
                    text = text2
                    j = j2
                    elapsed = elapsed2 or elapsed
                if j:
                    ans = j.get("answer")
                    success = True
                else:
                    # fallback: last non-empty line
                    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
                    ans = lines[-1] if lines else None
                    success = False
                    fallback = True
            rec = {"model": model_id, "trial": t, "prompt": p, "raw": text, "answer": ans, "success": success, "error": None, "time": elapsed, "fallback": fallback}
            print("Recorded answer:", ans, "time=", elapsed, "fallback=", fallback)
            records.append(rec)

    # write json and csv
    with open(json_path, "w") as jf:
        json.dump(records, jf, indent=2)
    with open(csv_path, "w", newline='') as cf:
        writer = csv.DictWriter(cf, fieldnames=["model", "trial", "prompt", "answer", "success", "fallback", "time", "error"])
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k) for k in writer.fieldnames})

    try:
        model.unload()
    except Exception:
        pass

    # summary
    total = len(records)
    successes = sum(1 for r in records if r.get("success"))
    avg_time = sum((r.get("time") or 0) for r in records) / total if total else 0
    summary = {"model": model_id, "timestamp": timestamp, "total": total, "successes": successes, "success_rate": successes/total if total else 0, "avg_time_s": avg_time, "json_path": json_path, "csv_path": csv_path}
    print("\nSummary:", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Model id to test (e.g., qwen3.5-2b)")
    parser.add_argument("--trials", type=int, default=3)
    args = parser.parse_args()

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
    ]

    summary = run_trials(args.model, prompts, trials=args.trials)
    print(json.dumps(summary, indent=2))
