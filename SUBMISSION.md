# HW4 — submission

**AI assistance:** <!-- what you used, and for what. "None" is an answer too. -->
> 
---

## Part A — Plan on paper (Easy)

> Commit this whole part before any `.py` file exists.

### A1 — The steps

| # | Step                        | What goes in (types)                             | What comes out (types)            | When it goes wrong                                                                              | Tool, loop, or model? |
|---|-----------------------------|--------------------------------------------------|-----------------------------------|-------------------------------------------------------------------------------------------------|-----------------------|
| 1 | Define what to search for   | Users Q (str)                                    | District name and metrics (str)   | Model confuses metrics or invents a non‑existent district                                       | Model                 |
| 2 | Get facts                   | District name (str) and what we loking wor (str) | Num (float) and Doc ID (str)      | There is a typo in the name; an archived profile has been found, but no data has been retrieved | Tool (lookup)         |
| 3 | Calculate density           | Math (FE: 44675 / 921.4) (str)                   | Result (float)                    | Division by zero, incorrect syntax                                                              | Tool (calculate)      |
| 4 | Compare and find difference | Math expression for substraction                 | Result (float)                    | Syntax error                                                                                    | Tool (calculate)      |
| 5 | Collect answers             | Results of calc                                  | Final "ANSWER: name/number" (str) | The model forgot to round or outputted the wrong format                                         | Model                 |

**How the steps connect:**

<!-- which step feeds which: a list, an ASCII diagram, or an image committed to the repo -->

1 -> 2 -> 3 -> 4 -> 5.
The model reads the question (Step 1) and calls the lookup tool to retrieve the facts (population and area) for each district (Step 2). The model sends the obtained numbers to the calculate tool to calculate the density (Step 3), and then again to calculate to find the difference (Step 4). The model compiles the final figures into the final answer according to the required template (Step 5).

**What I am assuming:**

<!-- census year, archived profiles, corrections, units, where rounding happens, ... -->

We always use the latest figures from the census and budgets for 2025. Our code should ignore old profiles (marked as ARCHIVED 2019). If there is a separate correction document (Correction), we trust it, not the profile with the error. We perform all rounding only at the very end for the final answer (based on the decimals parameter) so as not to compromise accuracy.

### A2 — The two tools

#### `lookup`

```json
{
  "name": "lookup",
  "description": "Finds facts about a district in the Nine Rivers Region. Use it to get data like population, budget, or area.",
  "parameters": {
    "type": "object",
    "properties": {
      "district": {
        "type": "string",
        "description": "Name of the district, for example 'Ossbridge'"
      },
      "topic": {
        "type": "string",
        "description": "What to look for, like 'population', 'schools', or 'water'"
      }
    },
    "required": ["district", "topic"]
  }
}
```

| Case                | What the tool returns                                                |
|---------------------|----------------------------------------------------------------------|
| success             | Short string with the answer and the document ID                     |
| wrong spelling/typo | An error message suggesting the correct name ( Ossbridge or Ossford) |
| archived profile | It ignores the old 2019 file and returns only the fresh 2025 data    |
| not found | An error saying the data does not exist in the documents             |

**Worst thing it could do with strange or dangerous input: **
* Model could send a huge garbage string in topic, and if the tool returns too much text back, it will waste a lot of API tokens and money.
#### `calculate`

```json
{
  "name": "calculate",
  "description": "Does math calculations. Always use this instead of guessing the math yourself.",
  "parameters": {
    "type": "object",
    "properties": {
      "expression": {
        "type": "string",
        "description": "A mathematical expression with numbers and standard operators (+, -, *, /). Example: '44675 / 921.4'"
      }
    },
    "required": ["expression"]
  }
}
```

| Case | What the tool returns                                    |
|---|----------------------------------------------------------|
| success | The calculated number                                    |
| division by zero | An error message "Cannot divide by zero"                 |
| strange characters | An error message "Invalid characters in math expression" |
| number is too huge | An error message "Result is too large"                   |

**Worst thing it could do with strange or dangerous input:**
* The model could try to send a harmful Python command like __import__('os') instead of math. If I used eval(), it could hack or crash my computer, so I must block this.

### A3 — Q-09 by hand

```json
[
  {
    "role": "user",
    "content": "Which district has the higher population density in 2025, Brightwater or Millbrook, and by how many residents per square kilometre?"
  },
  {
    "role": "assistant",
    "tool_calls": [
      {
        "id": "call_001",
        "type": "function",
        "function": {
          "name": "lookup",
          "arguments": "{\"district\": \"Brightwater\", \"topic\": \"population and area\"}"
        }
      },
      {
        "id": "call_002",
        "type": "function",
        "function": {
          "name": "lookup",
          "arguments": "{\"district\": \"Millbrook\", \"topic\": \"population and area\"}"
        }
      }
    ]
  },
  {
    "role": "tool",
    "tool_call_id": "call_001",
    "content": "[NR-05, NR-16] 2025 Population: 44,675. Area: 921.4 sq km (corrected)."
  },
  {
    "role": "tool",
    "tool_call_id": "call_002",
    "content": "[NR-11] 2025 Population: 37,203. Area: 758.6 sq km."
  },
  {
    "role": "assistant",
    "tool_calls": [
      {
        "id": "call_003",
        "type": "function",
        "function": {
          "name": "calculate",
          "arguments": "{\"expression\": \"44675 / 921.4\"}"
        }
      },
      {
        "id": "call_004",
        "type": "function",
        "function": {
          "name": "calculate",
          "arguments": "{\"expression\": \"37203 / 758.6\"}"
        }
      }
    ]
  },
  {
    "role": "tool",
    "tool_call_id": "call_003",
    "content": "48.486"
  },
  {
    "role": "tool",
    "tool_call_id": "call_004",
    "content": "49.041"
  },
  {
    "role": "assistant",
    "tool_calls": [
      {
        "id": "call_005",
        "type": "function",
        "function": {
          "name": "calculate",
          "arguments": "{\"expression\": \"49.041 - 48.486\"}"
        }
      }
    ]
  },
  {
    "role": "tool",
    "tool_call_id": "call_005",
    "content": "0.555"
  },
  {
    "role": "assistant",
    "content": "ANSWER: Millbrook | 0.6"
  }
]
```

**My arithmetic:**
* Brightwater density: 44675 / 921.4 = 48.486... residents/km2 (using the corrected area from NR-16)
* Millbrook density: 37203 / 758.6 = 49.041... residents/km2
* Difference: 49.041 - 48.486 = 0.555 residents/km2
* Rounded to 1 decimal (as required by the question): 0.6
* Millbrook is denser

### A4 — Why I split it this way

<!-- one other way to split the task, and why you did not choose it -->
> I could have made just one big tool called answer_question that takes the user's question, searches the files, does the math in Python, and returns the final answer. I didnt choose this because it defeats the purpose of using an LLM. Model would just pass the string to my code without doing any reasoning. Also, writing a Python script to automatically understand and calculate any possible question would be too hard. Splitting the task into small tools (lookup and calculate) lets the model handle the logic and planning, while my code handles the facts and the math.

---

## Part B — Build it and run it (Medium)

### What I changed from Part A while coding

<!-- what changed in your plan, and why. "None" is an answer too. -->

### B2 — Tests

```text
<!-- pytest output -->
```

### B3 — The loop

- Round limit, and why:
- Where the logs are:
- Real Q-09 conversation compared with my A3 version, what is different:

### B4 — Three strategies

**What I kept the same:**

<!-- model, temperature, k, prompts, answer format, anything else -->

**My rule for a correct answer** (written before the first full run):

| Run | Strategy | Correct /20 | Unanswered | Input tokens | Output tokens | Median seconds per question | Total seconds | Cost ($) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | S1 direct | | | | | | | |
| 1 | S2 think and vote (k = ) | | | | | | | |
| 1 | S3 tools | | | | | | | |
| 2 | S1 direct | | | | | | | |
| 2 | S2 think and vote (k = ) | | | | | | | |
| 2 | S3 tools | | | | | | | |

**Per question (run 1):**

| Question | S1 | S2 | S3 |
|---|:---:|:---:|:---:|
| Q-01 | | | |
| Q-02 | | | |
| Q-03 | | | |
| Q-04 | | | |
| Q-05 | | | |
| Q-06 | | | |
| Q-07 | | | |
| Q-08 | | | |
| Q-09 | | | |
| Q-10 | | | |
| Q-11 | | | |
| Q-12 | | | |
| Q-13 | | | |
| Q-14 | | | |
| Q-15 | | | |
| Q-16 | | | |
| Q-17 | | | |
| Q-18 | | | |
| Q-19 | | | |
| Q-20 | | | |

---

## Part C — Explain and choose (Hard)

### C1 — Does the tool description matter?

| Question | Calls (your description) | Calls (vague) | Answer (yours) | Answer (vague) |
|---|---:|---:|---|---|
| | | | | |

### C2 — Three mistakes explained

### C3 — Which strategy I would use, and what would change it

### C4 — How sure I can be

### Final questions

1.
2.
3.
4.
5.
6.
7.
8.
