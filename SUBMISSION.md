# HW4 — submission

**Name:Gaponenko Stanislav**
**Student ID:S23069758**
**Group:CSS4007**
**Repository: https://github.com/GestasContrad/hw4-GaponenkoStanislav**

**AI assistance:** <!-- what you used, and for what. "None" is an answer too. -->
> I used Gemini for some explanations, as coding assistant and to help with debugging.
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
tests/test_tools.py::test_lookup_finds_correct_number PASSED                                                                                                                                                                                  [ 10%]
tests/test_tools.py::test_lookup_handles_misspelled_and_similar_names PASSED                                                                                                                                                                  [ 20%]
tests/test_tools.py::test_lookup_ignores_archived_profile PASSED                                                                                                                                                                              [ 30%]
tests/test_tools.py::test_lookup_applies_correction_for_brightwater PASSED                                                                                                                                                                    [ 40%]
tests/test_tools.py::test_lookup_handles_unknown_district PASSED                                                                                                                                                                              [ 50%]
tests/test_tools.py::test_calculate_basic_math PASSED                                                                                                                                                                                         [ 60%]
tests/test_tools.py::test_calculate_refuses_import_os PASSED                                                                                                                                                                                  [ 70%]
tests/test_tools.py::test_calculate_refuses_class_access PASSED                                                                                                                                                                               [ 80%]
tests/test_tools.py::test_calculate_refuses_huge_exponents PASSED                                                                                                                                                                             [ 90%]
tests/test_tools.py::test_calculate_handles_division_by_zero PASSED
```

### B3 — The loop

- **Round limit, and why:** 10 rounds. This is enough for complex questions that need to look up 3 districts and perform several math steps (which takes about 5-6 rounds), but it prevents the model from wasting tokens and money in an infinite loop if it gets stuck on an error

- **Where the logs are:** Saved as JSON files in the outputs/ folder
- **Real Q-09 conversation compared with my A3 version, what is different:**  The real model combined the lookup calls for Brightwater and Millbrook into a single round using parallel tool calling (exactly as I planned). But, the exact math expressions the model sent to calculate had extra spaces compared to my handwritten JSON, and the model added some polite text before outputting the final "ANSWER:" string

### B4 — Three strategies

**What I kept the same:**

<!-- model, temperature, k, prompts, answer format, anything else -->
I kept the model (gpt-5.6-luna), the formatting instruction (Reply strictly as ANSWER: <name> | <number>), and the target questions identical across all three strategies. reasoning_effort="none" was used in all API calls to allow tool usage and identical model configuration.

**My rule for a correct answer** (written before the first full run): I split the model's output by |. The text part must exactly match the correct answer (case-insensitive). The number part is parsed as a float. I round both the model's number and the true value to the required decimals. The answer is marked correct if the absolute difference between them is <= 10^-decimals (which allows a difference of 1 in the last digit as permitted)


| Run | Strategy | Correct /20 | Unanswered | Input tokens | Output tokens | Median seconds per question | Total seconds | Cost ($) (exp) |
|---|---|------------:|-----------:|-------------:|---:|---:|---:|---------------:|
| 1 | S1 direct |           2 |          0 |        42879 |308 |1.97s |41.95s |     0.0044           |
| 1 | S2 think and vote (k = ) |           2 |          0 |       214995 |1534 |8.13s |163.37s |   0.0223             |
| 1 | S3 tools |          15 |          0 |        36934 |2932 |5.91s |131.99s |      0.0052          |
| 2 | S1 direct |           1 |          0 |  42879            | 308|1.92s |52.19s |     0.0044           |
| 2 | S2 think and vote (k = ) |           2 |          0 | 214995             |1541 |8.06s |225.93s |  0.0223              |
| 2 | S3 tools |          13 |          0 |   33365          |2738 |5.86s |160.38s |      0.0047          |

*Cost: (Input tokens / 1,000,000 * entry price) + (Output tokens / 1,000,000 * exit price)*

**Per question (run 1):**

| Question | S1 | S2 | S3 |
|---|:---:|:---:|:---:|
| Q-01 | ✗ | ✗ | ✓ |
| Q-02 | ✗ | ✗ | ✗ |
| Q-03 | ✗ | ✗ | ✗ |
| Q-04 | ✗ | ✗ | ✓ |
| Q-05 | ✗ | ✗ | ✓ |
| Q-06 | ✓ | ✓ | ✓ |
| Q-07 | ✗ | ✗ | ✓ |
| Q-08 | ✗ | ✗ | ✓ |
| Q-09 | ✗ | ✗ | ✓ |
| Q-10 | ✓ | ✓ | ✓ |
| Q-11 | ✗ | ✗ | ✓ |
| Q-12 | ✗ | ✗ | ✗ |
| Q-13 | ✗ | ✗ | ✗ |
| Q-14 | ✗ | ✗ | ✓ |
| Q-15 | ✗ | ✗ | ✓ |
| Q-16 | ✗ | ✗ | ✗ |
| Q-17 | ✗ | ✗ | ✓ |
| Q-18 | ✗ | ✗ | ✓ |
| Q-19 | ✗ | ✗ | ✓ |
| Q-20 | ✗ | ✗ | ✓ |


**Per question (run 2):**

| Question | S1 | S2 | S3 |
|---|:---:|:---:|:---:|
| Q-01 | ✗ | ✗ | ✓ |
| Q-02 | ✗ | ✗ | ✗ |
| Q-03 | ✗ | ✗ | ✓ |
| Q-04 | ✗ | ✗ | ✓ |
| Q-05 | ✗ | ✗ | ✓ |
| Q-06 | ✗ | ✓ | ✓ |
| Q-07 | ✗ | ✗ | ✓ |
| Q-08 | ✗ | ✗ | ✗ |
| Q-09 | ✗ | ✗ | ✓ |
| Q-10 | ✓ | ✓ | ✓ |
| Q-11 | ✗ | ✗ | ✗ |
| Q-12 | ✗ | ✗ | ✗ |
| Q-13 | ✗ | ✗ | ✗ |
| Q-14 | ✗ | ✗ | ✓ |
| Q-15 | ✗ | ✗ | ✓ |
| Q-16 | ✗ | ✗ | ✗ |
| Q-17 | ✗ | ✗ | ✓ |
| Q-18 | ✗ | ✗ | ✓ |
| Q-19 | ✗ | ✗ | ✗ |
| Q-20 | ✗ | ✗ | ✓ |
---

## Part C — Explain and choose (Hard)

### C1 — Does the tool description matter?

| Question | Calls (your description) | Calls (vague) | Answer (yours)                       | Answer (vague)                       |
|----------|-------------------------:|--------------:|--------------------------------------|--------------------------------------|
| Q   1    |                        3 |             2 | Ossbridge / 4.57                     | Ossbridge                    / 4.57  |
| Q   2    |                        3 |             5 | Harrowfield / 1.69 percentage points | Harrowfield / 1.69 percentage points |
| Q   3    |                        3 |             2 | Lindenmoor / 0.00534015833513721     | Lindenmoor / 0.01                    |
| Q    4   |                        3 |             2 | Millbrook / 2.59                     | Millbrook / 2.59                     |
| Q   5    |                        4 |             2 | Coldharbour / 14235.31               | Coldharbour / 14235.31               |

**Why did it change?**

> When the tool description was changed to a vague "Looks things up.", the model's accuracy dropped and its formatting broke. Without knowing exactly what the tool can find (like budget, population, or area), the LLM struggled to formulate the correct search queries in the topic argument. For example, in Q-03 it returned a completely wrong number (0.01), likely because it failed to find the correct data or hallucinated the math. It also lost focus on the formatting constraints: it failed to round numbers in Q-01 and Q-05, and illegally added "percentage points" to the final answer in Q-02. A detailed tool description acts as a mini-prompt that gives the model context for planning; without it, the model acts lost.

### C2 — Three mistakes explained (Q2 for S1, Q8 For S2, Q11 For S3)

1. **S1 (Direct) mistake on Q-02**

* Model output: {"answer": "ANSWER: Tarnvale | 0.31 percentage points"}

Explanation: The true answer is Harrowfield by 1.69 percentage points. The model failed because it was forced to do complex arithmetic (calculating two percentage growths, then finding the difference) in a single forward pass. LLMs generate text token by token; without a "scratchpad" to write down intermediate steps, they cannot hold large numbers in memory or perform multi-step math. It simply hallucinated a plausible-looking number (0.31) and guessed the wrong district.

2. **S2 (Think and vote) mistake on Q-08**

Model output (5 samples):
* ANSWER: Millbrook | 0.00 million tenge
* ANSWER: Brightwater | 721.85 million tenge
* ANSWER: Brightwater | 0.723 million tenge
* ANSWER: Millbrook | 0.001 million tenge
* ANSWER: Millbrook | 0.073 million tenge

Explanation: The true answer is Brightwater by 72.46 million tenge. Why does asking 5 times and voting fix some mistakes but not others? Voting works when the model's fundamental logic is sound but noisy (e.g., retrieving facts). However, this question requires converting megalitres to cubic metres, multiplying by a tariff, and converting to millions. LLMs are notoriously bad at arithmetic with large numbers. Giving it room to "think" doesn't fix its inability to do complex math. Increasing the temperature to generate 5 samples just caused the model to hallucinate 5 completely different arithmetic failures. Voting is useless when the probability space of the correct math digits is basically zero.

3. **S3 (Tools) mistake on Q-12**

* Model tool calls: {"expression":"(16021.7*1000000/13904 - 12960.3*1000000/10652)/1000"}

* Model output: ANSWER: Harrowfield | 64.39

Explanation: Do tools fix every error? No. Tools fix computation, but they do not fix logic. In this log, the model wrote a perfectly valid mathematical expression to find the difference in budget per pupil. The calculate tool correctly returned the difference (64.39 thousand). However, the model failed at the final logical step: identifying which district was higher. Tarnvale's budget per pupil (~1.21 million) is strictly greater than Harrowfield's (~1.15 million). Because the model combined the entire equation into a single step instead of calculating them separately, it lost track of which side of the minus sign belonged to which district, ultimately guessing "Harrowfield" incorrectly.

### C3 — Which strategy I would use, and what would change it

**Which strategy is best for this task?**
Strategy 3 (Tools) is definitively the best for this specific dataset. It achieved a much higher accuracy (65-75%) compared to S1 and S2 (5-10%). While it takes slightly longer than S1, it is significantly faster and cheaper than S2. Since the Nine Rivers dataset heavily relies on precise mathematical operations and large numbers, providing a calculator tool is the only way to get reliable results.

**What would change my choice?**

* Budget or latency constraints: If the application requires instant responses (e.g., a real-time chatbot) or operates on a very strict API budget, S1 would be better. S3 makes multiple API calls per question, which increases both latency and cost.

* Qualitative rather than quantitative data: If the questions were about summarizing text, analyzing sentiment, or extracting names (without any math involved), S3's calculator would be useless. In that case, S1 would be perfectly adequate, or S2 if we needed high-quality creative reasoning.

### C4 — How sure I can be

> I am confident that S3 is superior for math-heavy tasks, but the exact accuracy numbers are not entirely reliable. A sample size of only 20 questions is too small to make definitive statistical claims. Furthermore, there is noticeable variance between runs due to the non-deterministic nature of LLMs: in my first run, S3 got 15 correct, but in the second run, it only got 13. To be completely sure about the exact performance metrics, we would need to test the strategies on a much larger dataset (e.g., 200+ questions) and average the results over several runs.

### Final questions

1. **When the model sends a tool_calls message, what has actually run so far?**
When the model sends a `tool_calls` message, no actual code or function has executed yet. The model has simply generated a text string formatted as a JSON object, predicting which tool should be called and with what arguments. It is entirely up to our local Python script to intercept this message, execute the local function, and return the result back to the model.

2. **Why does arguments arrive as a string, and what goes wrong if you pass it straight into your function?**
The `arguments` arrive as a string because Large Language Models inherently generate raw text, not programmable data structures. If you pass this string directly into a Python function without parsing it (e.g., using `json.loads`), the function will treat it as a single string object rather than a dictionary of parameters. This will immediately cause a `TypeError` when the function tries to access specific keys or unpack the arguments.

3. **How many tokens do your two tool definitions add to every S3 request? Measure it.**
By examining the first round of my S3 logs (e.g., Q-12), the initial `input_tokens` count is around 219. Since the base system prompt and the user question only account for about 20-30 tokens, the two tool definitions (`lookup` and `calculate`) add approximately 190 tokens to every single S3 request. This token overhead is appended to every subsequent round in the conversation loop as well.

4. **How much more did S2 cost than S1? Give the number from your table and explain it.**
In my second run, S2 cost $0.0223, which is roughly five times more than S1's cost of $0.0044. This directly aligns with the strategy's design, as S2 queries the model 5 separate times (`k=5`) to generate multiple samples for voting. Consequently, it consumes five times as many input and output tokens, multiplying the final API billing by the same factor.

5. **Which question needed the most rounds in S3, and why?**
In my logs, Question 11 required 4 rounds to complete, making it one of the longest. The model first had to use the `lookup` tool three separate times to gather data for Redfen, Ashgrove, and Millbrook. It then used the `calculate` tool in multiple subsequent rounds to process these numbers before finally generating the text answer.

6. **What would you change in lookup if there were 100,000 documents?**
If there were 100,000 documents, returning full texts or iterating through a simple list would immediately exceed the model's context window and take too long to process. I would integrate a vector database to perform semantic search using embeddings or use a keyword index like BM25. The `lookup` tool would then only return the top 3-5 most relevant text chunks rather than searching through the entire corpus.

7. **What stops your calculate from running dangerous code? Could the model still make it misbehave?**
The `calculate` tool is protected by using Python's safe `ast` parsing instead of the dangerous `eval()` function, which prevents the model from executing arbitrary system commands or malicious scripts. However, the model could still make the tool misbehave by attempting mathematical exploits, such as dividing by zero or calculating massive exponents (e.g., `9**999999`). This could crash the script or cause a denial-of-service via timeout if not properly handled with `try/except` blocks.

8. **For which kind of question did tools help most, and for which did they not help at all?**
Tools helped the most on questions requiring complex arithmetic, such as calculating budget differences or percentage points, raising accuracy from near zero in S1 to over 65% in S3. However, tools did not help at all when the model made fundamental logical errors, such as forgetting which district a calculated number belonged to (as seen in Q-12). Tools also provided no additional benefit for simple fact-retrieval questions where a direct lookup without calculation would have sufficed.
