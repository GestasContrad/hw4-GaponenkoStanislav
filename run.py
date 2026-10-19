import json
import time
import os
import math
from collections import Counter
from openai import OpenAI
from dotenv import load_dotenv
from strategies import run_s3_tools

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("data/questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

with open("data/corpus.jsonl", "r", encoding="utf-8") as f:
    DOCS_TEXT = "\n\n".join(
        [f"[{json.loads(line)['id']}] {json.loads(line)['title']}\n{json.loads(line)['text']}" for line in f])


def check_answer(predicted_str, true_name, true_val, decimals):
    if predicted_str == "UNANSWERED" or "ANSWER:" not in predicted_str:
        return False
    try:
        ans = predicted_str.split("ANSWER:")[-1].strip()
        name_part, val_part = ans.split("|")
        name_part = name_part.strip().lower()
        val_part = float(val_part.strip().replace(',', ''))

        if name_part != true_name.lower():
            return False

        # allow dif of 1 in the last digit (FE: 0.1 if decimals=1).
        tolerance = (10 ** -decimals) + 1e-9
        diff = abs(val_part - true_val)
        return round(diff, decimals) <= tolerance
    except Exception:
        return False


def run_s1(q):
    # strict with all
    prompt = f"Here are the documents about the Nine Rivers Region:\n\n{DOCS_TEXT}\n\nQuestion: {q['question']}\n\nReply strictly as ANSWER: <name or yes/no> | <number>"
    start = time.time()
    resp = client.chat.completions.create(
        model="gpt-5.6-luna",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        reasoning_effort="none"
    )
    dur = time.time() - start
    return resp.choices[0].message.content, dur, resp.usage.prompt_tokens, resp.usage.completion_tokens


def run_s2(q, k=5):
    # think and vote (5 req)
    prompt = f"Here are the documents about the Nine Rivers Region:\n\n{DOCS_TEXT}\n\nQuestion: {q['question']}\n\nThink step by step. Then reply strictly as ANSWER: <name or yes/no> | <number>"

    answers = []
    total_in = 0
    total_out = 0
    start = time.time()

    for _ in range(k):
        resp = client.chat.completions.create(
            model="gpt-5.6-luna",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            reasoning_effort="none"
        )
        answers.append(resp.choices[0].message.content)
        total_in += resp.usage.prompt_tokens
        total_out += resp.usage.completion_tokens

    dur = time.time() - start

    final_lines = []
    for a in answers:
        if "ANSWER:" in a:
            final_lines.append(a[a.find("ANSWER:"):].strip())

    if not final_lines:
        best_ans = "UNANSWERED"
    else:
        best_ans = Counter(final_lines).most_common(1)[0][0]

    return best_ans, dur, total_in, total_out, answers


def run_all():
    for folder in ["S1", "S2", "S3"]:
        os.makedirs(f"outputs/run1/{folder}", exist_ok=True)

    results = {"S1": [], "S2": [], "S3": []}

    for q in QUESTIONS:
        print(f"\nRunning {q['id']}")

        print("S1 (Direct)...")
        ans1, dur1, in1, out1 = run_s1(q)
        corr1 = check_answer(ans1, q['answer'], q['value'], q['decimals'])
        results["S1"].append({"id": q['id'], "ans": ans1, "correct": corr1, "dur": dur1, "in": in1, "out": out1})

        with open(f"outputs/run1/S1/{q['id']}_log.json", "w", encoding="utf-8") as f:
            json.dump({"answer": ans1, "duration": dur1, "in_tokens": in1, "out_tokens": out1}, f, indent=2)

        print("S2 (Think and vote)...")
        ans2, dur2, in2, out2, logs2 = run_s2(q)
        corr2 = check_answer(ans2, q['answer'], q['value'], q['decimals'])
        results["S2"].append({"id": q['id'], "ans": ans2, "correct": corr2, "dur": dur2, "in": in2, "out": out2})

        with open(f"outputs/run1/S2/{q['id']}_log.json", "w", encoding="utf-8") as f:
            json.dump(logs2, f, indent=2)

        print("S3 (Tools)...")
        ans3, logs3 = run_s3_tools(f"{q['question']} Reply strictly as ANSWER: <name or yes/no> | <number>", q['id'])
        dur3 = sum(r['duration'] for r in logs3)
        in3 = sum(r['input_tokens'] for r in logs3)
        out3 = sum(r['output_tokens'] for r in logs3)
        corr3 = check_answer(ans3, q['answer'], q['value'], q['decimals'])
        results["S3"].append({"id": q['id'], "ans": ans3, "correct": corr3, "dur": dur3, "in": in3, "out": out3})

        with open(f"outputs/run1/S3/{q['id']}_log.json", "w", encoding="utf-8") as f:
            json.dump(logs3, f, indent=2)

    print("\nRESULTS")
    for strat, data in results.items():
        correct = sum(1 for d in data if d['correct'])
        unanswered = sum(1 for d in data if d['ans'] == "UNANSWERED")
        tot_in = sum(d['in'] for d in data)
        tot_out = sum(d['out'] for d in data)
        tot_dur = sum(d['dur'] for d in data)

        times = sorted([d['dur'] for d in data])
        median_dur = times[len(times) // 2] if times else 0

        print(f"{strat}: Correct: {correct}, Unanswered: {unanswered}, InTokens: {tot_in}, OutTokens: {tot_out}, MedianTime: {median_dur:.2f}s, TotalTime: {tot_dur:.2f}s")

    print("\nPER QUESTION TABLE")
    print("| Question | S1 | S2 | S3 |")
    print("|---|:---:|:---:|:---:|")
    for i in range(len(QUESTIONS)):
        q_id = results["S1"][i]["id"]
        c1 = "✓" if results["S1"][i]["correct"] else "✗"
        c2 = "✓" if results["S2"][i]["correct"] else "✗"
        c3 = "✓" if results["S3"][i]["correct"] else "✗"
        print(f"| {q_id} | {c1} | {c2} | {c3} |")


if __name__ == "__main__":
    run_all()