import json
import ast
import operator
import difflib
from pathlib import Path


def load_corpus():
    docs = []
    path = Path("data/corpus.jsonl")
    if not path.exists():
        return docs
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line.strip()))
    return docs

CORPUS = load_corpus()
DISTRICTS = [
    "Ossbridge", "Ossford", "Tarnvale", "Kelmarsh", "Brightwater",
    "Stonecairn", "Harrowfield", "Lindenmoor", "Redfen", "Ashgrove",
    "Millbrook", "Coldharbour"
]


def lookup(district: str, topic: str) -> str:

    matches = difflib.get_close_matches(district, DISTRICTS, n=2, cutoff=0.5)

    if district not in DISTRICTS:
        if len(matches) > 1:
            return f'{{"error": "no district named {district}; did you mean {" or ".join(matches)}?"}}'
        elif len(matches) == 1:
            district = matches[0]  #auto fix if 1 res
        else:
            return f'{{"error": "no district named {district} found."}}'

    results = []
    for doc in CORPUS:
        title = doc.get("title", "")

        if "ARCHIVED" in title:
            continue

        if district.lower() in title.lower() or (doc["id"] == "NR-15" and "water" in topic.lower()):
            results.append(f"[{doc['id']}] {title}: {doc['text'][:500]}")

        if district == "Brightwater" and doc["id"] == "NR-16":
            results.append(f"[{doc['id']}] {title}: {doc['text']}")

    if not results:
        return '{"error": "Data not found for this request."}'

    return "\n".join(results)


def calculate(expression: str) -> str:
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos
    }

    def eval_node(node):
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise ValueError("Only numbers are allowed")
            return node.value
        elif isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)

            if isinstance(node.op, ast.Pow):
                if right > 100 or left > 1000000:
                    raise ValueError("Numbers too large for exponentiation")

            if isinstance(node.op, ast.Div) and right == 0:
                raise ZeroDivisionError("division by zero")

            op = allowed_operators.get(type(node.op))
            if not op:
                raise ValueError("Unsupported operator")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = eval_node(node.operand)
            op = allowed_operators.get(type(node.op))
            return op(operand)
        else:
            raise ValueError("Unsupported syntax")

    try:
        # not script
        tree = ast.parse(expression, mode='eval')
        result = eval_node(tree.body)

        if isinstance(result, (int, float)) and abs(result) > 1e100:
            return '{"error": "Result is too large"}'

        return str(result)
    except Exception as e:
        return f'{{"error": "{str(e)}"}}'