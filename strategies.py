import json
import time
import os
from openai import OpenAI
from dotenv import load_dotenv
from tools import lookup, calculate

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup",
            "description": "Looks things up.",
            "parameters": {
                "type": "object",
                "properties": {
                    "district": {"type": "string"},
                    "topic": {"type": "string"}
                },
                "required": ["district", "topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Does math calculations. Always use this instead of guessing the math yourself.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        }
    }
]


def run_s3_tools(question_text: str, question_id: str, max_rounds: int = 10):
    messages = [{"role": "user", "content": question_text}]
    log_data = []

    for round_num in range(max_rounds):
        start_time = time.time()

        response = client.chat.completions.create(
            model="gpt-5.6-luna",
            messages=messages,
            tools=TOOLS,
            reasoning_effort="none"
        )

        msg = response.choices[0].message
        duration = time.time() - start_time

        log_data.append({
            "round": round_num + 1,
            "duration": round(duration, 2),
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "tool_calls": [tc.model_dump() for tc in (msg.tool_calls or [])],
            "content": msg.content
        })

        if not msg.tool_calls:
            return msg.content, log_data

        messages.append(msg)

        for tool_call in msg.tool_calls:
            tool_name = tool_call.function.name

            # json validation
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                result = '{"error": "Invalid JSON arguments"}'
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
                continue

            if tool_name == "lookup":
                result = lookup(args.get("district", ""), args.get("topic", ""))
            elif tool_name == "calculate":
                result = calculate(args.get("expression", ""))
            else:
                result = f'{{"error": "Unknown tool {tool_name}"}}'

            # ans on every tool_call_id
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})

    return "UNANSWERED", log_data


def save_log(question_id, data, strategy):
    os.makedirs("outputs", exist_ok=True)
    with open(f"outputs/{strategy}_{question_id}_log.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    q09_text = "Which district has the higher population density in 2025, Brightwater or Millbrook, and by how many residents per square kilometre? Reply strictly as ANSWER: <name> | <number>"
    print("Running Q-09...")
    answer, logs = run_s3_tools(q09_text, "Q-09")
    save_log("Q-09", logs, "S3")
    print(f"\nFinal Answer: {answer}")
    print(f"Total rounds: {len(logs)}")