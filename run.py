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
    os.makedirs("outputs/vague_test", exist_ok=True)

    for q in QUESTIONS[:5]:
        print(f"\nRunning {q['id']} (Vague Description Test)")

        ans3, logs3 = run_s3_tools(f"{q['question']} Reply strictly as ANSWER: <name or yes/no> | <number>", q['id'])

        calls_count = len(logs3) - 1

        print(f"Answer (vague): {ans3}")
        print(f"Tool calls rounds: {calls_count}")

        with open(f"outputs/vague_test/{q['id']}_vague_log.json", "w", encoding="utf-8") as f:
            json.dump(logs3, f, indent=2)


if __name__ == "__main__":
    run_all()