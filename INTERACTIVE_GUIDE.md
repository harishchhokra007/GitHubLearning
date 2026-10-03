# INTERACTIVE SYSTEM GUIDE

## Starting the System

```powershell
cd C:\repos\ai-engineering-lead
python main.py
```

You'll see:
```
Enter your query:
```

Now you can ask questions!

---

## Example Session

### Step 1: Ask a Question
```
Enter your query: What are the work hour policies?
```

### Step 2: System Processes

Behind the scenes, 5 agents work together:
1. **Orchestrator** breaks down your question
2. **Retriever** searches documents for relevant information
3. **Analyzer** synthesizes information across documents
4. **Verifier** validates the answer and checks for issues
5. **Memory** tracks context for follow-up questions

### Step 3: You Get an Answer

```
ANSWER:
Based on the retrieved documents, here's a comprehensive answer to your query:

Query: What are the work hour policies?

Key Findings:

1. From Employee Handbook:
   EMPLOYEE HANDBOOK: Work hours are 9am-5pm. Remote work available 2 days 
   per week. Vacation days provided annually.

Note: This answer is synthesized from 1 source(s).

======================================================================
SOURCES:

1. in_memory://Employee Handbook (Relevance: 0.62)

======================================================================
VERIFICATION:
- Grounded: True
- Grounding Score: 0.92
- Confidence: high
- Hallucinations Detected: False

======================================================================
EVALUATION:
- Retrieval Relevance: 0.62
- Failure Flags: 0

Execution Time: 208.97ms
======================================================================
```

---

## Understanding the Output

### The Answer
- Clear, comprehensive response to your question
- Key findings extracted from documents
- Practical and actionable information

### Sources
- Lists which documents were used
- Shows relevance score (0-1, higher = better match)
- You can verify by reading the original documents

### Verification Results

**Grounded: True/False**
- ✓ True: Answer is supported by document sources
- ✗ False: Answer not well-supported; take with caution

**Grounding Score (0-1)**
- 0.90-1.0: Excellent grounding ✓
- 0.70-0.89: Good grounding ✓
- 0.50-0.69: Moderate grounding (suggest follow-up)
- 0.30-0.49: Low grounding (verify with original documents)

**Confidence Level**
- **high**: Answer is well-grounded, no concerns
- **medium**: Answer is supported but may have minor issues
- **low**: Answer has concerns; recommend manual verification

**Hallucinations Detected: True/False**
- ✓ False: Answer only contains information from documents
- ⚠ True: Answer may contain information not in documents

### Evaluation Metrics

**Retrieval Relevance**
- Shows how well the documents matched your question
- Higher scores (0.7+) mean better document matches

**Failure Flags**
- Count of issues detected during processing
- 0 = no issues detected
- >0 = review the warnings section

**Execution Time**
- How long it took to process your query
- Typical: 200-500ms
- Longer for complex queries

---

## Tips for Better Results

### 1. Ask Clear Questions
```
GOOD:  "What are the key security requirements for accessing customer data?"
LESS:  "Tell me about security and data"

GOOD:  "How should employees report a policy violation?"
LESS:  "What's the process?"
```

### 2. Use Specific Keywords
```
GOOD:  "What is the remote work policy?"
LESS:  "Tell me about working from home"

GOOD:  "What are the data retention requirements?"
LESS:  "How long do we keep information?"
```

### 3. Ask Follow-Up Questions
```
Q1: "What is our remote work policy?"
    → You get the basic policy

Q2: "Can employees in Japan use this policy?"
    → You drill deeper on specific case

Q3: "What equipment or allowances are provided?"
    → You get practical details

Q4: "How is productivity monitored for remote workers?"
    → You get guardrails and expectations
```

### 4. Verify Low-Confidence Answers
If grounding score < 0.7 or confidence is "low":
- The system is uncertain
- Ask a follow-up question with different keywords
- Check the original documents manually
- Try rephrasing your question

---

## Common Query Patterns

### Pattern 1: Direct Factual Questions
```
"What are [specific thing]?"
"How many [specific metric]?"
"Who is responsible for [task]?"

Examples:
- What are the vacation days?
- How many sick days do employees get?
- Who approves expense reports?
```

### Pattern 2: Process Questions
```
"What is the process for [action]?"
"What are the steps to [goal]?"
"How do I [task]?"

Examples:
- What is the process for onboarding new employees?
- What are the steps to submit an expense report?
- How do I access the company VPN?
```

### Pattern 3: Compliance Questions
```
"What are the requirements for [area]?"
"What rules apply to [scenario]?"
"What is [policy name]?"

Examples:
- What are the security requirements?
- What rules apply to data sharing?
- What is the confidentiality agreement?
```

### Pattern 4: Synthesis Questions (Advanced)
```
"How do [policy A] and [policy B] work together?"
"What should happen if [scenario] occurs?"
"Compare [item 1] vs [item 2]?"

Examples:
- How do remote work and security policies align?
- What should happen if two policies conflict?
- Compare benefits across different employee types?
```

### Pattern 5: Scenario Questions (Complex Reasoning)
```
"An employee [situation]. Based on our policies, what should [outcome]?"

Examples:
- "An employee wants to work from Japan for 3 months. What policies apply?"
- "We need to share data with a vendor. What requirements must we meet?"
- "A manager needs to access terminated employee files. What rules govern this?"
```

---

## Iterative Questioning

The system works best when you ask questions iteratively:

**Session Example:**
```
Q1: "What is our remote work policy?"
    → You understand basic policy

Q2: "Are there any exceptions or special cases?"
    → You learn about edge cases

Q3: "How does this relate to our security policy?"
    → You see cross-document connections

Q4: "What about employees in other countries?"
    → You understand global implications

Q5: "What approval is needed for exceptions?"
    → You learn the decision process
```

Each answer builds context for better subsequent questions.

---

## Troubleshooting

### Q: I got a low grounding score, what should I do?
A: The answer may not be well-supported by documents.
   - Try a different phrasing of your question
   - Ask for more specific details
   - Check the original documents manually

### Q: The system didn't find relevant documents
A: The question may not match document content.
   - Use different keywords
   - Ask simpler, more specific questions
   - Check that documents are loaded (`python main.py --demo` to see sample docs)

### Q: I got a hallucination warning
A: The system detected information possibly not in documents.
   - Review the answer carefully
   - Compare with original sources
   - Ask for clarification on specific points

### Q: The system is slow
A: Processing complex queries takes time.
   - This is normal (200-500ms typical)
   - Complex queries with many agents take longer
   - If > 5 seconds, try restarting the system

### Q: Can I ask a follow-up question?
A: Yes! The system maintains context.
   - Ask follow-ups naturally
   - The Memory Agent tracks conversation history
   - You can reference previous answers

---

## Advanced Features

### 1. Hallucination Detection
The system automatically checks if answers contain information not in your documents.
- Detects unsupported claims
- Flags when answer is much longer than sources
- Provides warnings when detected

### 2. Grounding Verification
The system validates that answers come from your documents.
- Tracks which sources were used
- Calculates grounding score
- Shows confidence level

### 3. Execution Tracing
You can see how the system reasoned about your question.
- View which documents were retrieved
- See relevance scores
- Understand decision paths

### 4. Multi-Agent Reasoning
5 specialized agents work together:
- **Orchestrator**: Plans how to approach your question
- **Retriever**: Finds the most relevant documents
- **Analyzer**: Synthesizes information across documents
- **Verifier**: Validates the answer
- **Memory**: Maintains conversation context

---

## Demo Mode

To see the system in action with sample queries:

```powershell
python main.py --demo
```

This runs pre-loaded sample queries so you can see:
- How the system handles different question types
- What the output looks like
- Performance and timing
- Agent coordination

---

## Next Steps

1. **Start here**: `python main.py`
2. **Learn the system**: Read `SAMPLE_QUESTIONS.md`
3. **Understand the architecture**: Read `docs/ARCHITECTURE.md`
4. **Review implementation**: Read `docs/IMPLEMENTATION_SUMMARY.md`

---

## Quick Reference

| Task | Command |
|------|---------|
| Run interactive mode | `python main.py` |
| Run demo with samples | `python main.py --demo` |
| Run tests | `pytest tests/test_agents.py -v` |
| Verify installation | `python verify_installation.py` |
| View quick start | `cat QUICKSTART.md` |
| View sample questions | `cat SAMPLE_QUESTIONS.md` |
| View architecture | `cat docs/ARCHITECTURE.md` |
| View full implementation | `cat docs/IMPLEMENTATION_SUMMARY.md` |

---

## Summary

The Enterprise Knowledge Operations Agent is a multi-agent system that:

✓ Answers complex questions about your documents
✓ Synthesizes information across multiple sources
✓ Detects and reports hallucinations
✓ Validates grounding in source material
✓ Provides clear reasoning traces
✓ Maintains conversation context

**Ready to use! Start with: `python main.py`**
