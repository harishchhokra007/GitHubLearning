# Sample Questions for Enterprise Knowledge Agent

## Quick Copy-Paste Examples

Use these questions when you run `python main.py` to test the system:

---

## Category 1: Policy & Compliance Questions

### Simple Factual
```
"What are the work hour policies?"

"What is the vacation policy?"

"How many sick days do employees get?"

"What is the dress code?"

"What are the data protection requirements?"
```

### Cross-Document Synthesis
```
"How does our remote work policy align with our company culture values?"

"What are all the security requirements mentioned across our policies?"

"Compare employee benefits in the handbook versus the salary policy."

"What compliance rules apply to both HR and IT departments?"
```

---

## Category 2: Process & Procedure Questions

### Step-by-Step Procedures
```
"What are the steps for employee onboarding?"

"How do I submit an expense report?"

"What is the process for requesting time off?"

"How do I report a security breach?"

"What are the steps to access the company VPN?"
```

### Decision-Making
```
"When should I escalate an issue to management?"

"What are the approval thresholds for different expenses?"

"Under what conditions can employees work remotely?"

"When is IT security approval required for new software?"
```

---

## Category 3: Business Intelligence Questions

### Financial & Operations
```
"What is our target SLA for system uptime?"

"What are our cost control measures?"

"How are budgets allocated across departments?"

"What are the project approval requirements?"

"What metrics are we tracking for performance?"
```

### Strategic
```
"How does our IT infrastructure support business continuity?"

"What are the key risk areas mentioned in our policies?"

"How are confidentiality and data protection balanced with business needs?"

"What are our priorities for vendor management?"
```

---

## Category 4: Compliance & Legal Questions

### Regulatory
```
"What confidentiality obligations do we have?"

"What are the data retention requirements?"

"What are the intellectual property ownership rules?"

"What export control restrictions apply?"

"What are the non-disclosure agreement terms?"
```

### Risk & Liability
```
"What disclaimers are included in our service agreements?"

"What liability limitations apply to our services?"

"What warranty terms do we offer?"

"What indemnification clauses are in our contracts?"

"What are the consequences for policy violations?"
```

---

## Category 5: HR & People Questions

### Employment
```
"What benefits are provided for new hires?"

"What is the performance review process?"

"How is compensation determined?"

"What professional development opportunities exist?"

"What is the promotion criteria?"
```

### Workplace
```
"What is the anti-discrimination policy?"

"What harassment prevention measures are in place?"

"What accessibility accommodations are available?"

"What wellness programs are offered?"

"What is the grievance procedure?"
```

---

## Category 6: Complex Reasoning Questions

### Multi-Step Analysis
```
"A new engineer just joined the company. Based on our policies, what should 
happen in their first 30 days? What are all the compliance steps?"

"Our company wants to adopt a new data analytics tool. What security, 
compliance, and approval requirements would apply based on our policies?"

"An employee wants to work from Japan for 3 months while on the project team. 
What policies, approvals, and conditions would apply?"

"We need to share customer data with a third-party vendor. What contractual 
terms, security requirements, and approvals are needed?"
```

### Conflict Resolution
```
"If an employee wants to work remotely but their role requires on-site work, 
what policy provisions apply and what is the decision process?"

"What happens if a project deadline conflicts with data privacy requirements 
in our contracts?"

"An employee submitted an expense report that exceeds approval limits. What 
are the policies and next steps?"
```

---

## Category 7: Training & Knowledge Questions

### Understanding Policies
```
"Summarize the key points of the confidentiality policy in simple terms."

"What are the top 5 security practices employees should follow?"

"Explain the chain of command for incident reporting."

"What are the most important compliance rules for new employees?"

"What should every employee know about data protection?"
```

### Best Practices
```
"What does our policy say about best practices for password management?"

"What are the recommended steps for handling sensitive information?"

"What communication guidelines are recommended when discussing confidential matters?"

"What are the best practices for vendor selection based on our policies?"
```

---

## Category 8: Real-World Scenarios

### Practical Situations
```
"It's Friday at 4:55 PM and a critical system is down. What should happen 
based on our policies and escalation procedures?"

"An employee discovered a potential security vulnerability. What should they do?"

"The company received a legal subpoena for customer data. What policies apply?"

"An employee wants to start a side project that might compete with our business. 
What policy applies?"

"A vendor is asking for access to our internal systems. What approval process 
should we follow?"
```

### Troubleshooting
```
"An employee can't access the company network from home. What should they do 
and what are the security policies that apply?"

"A manager needs to access an employee's files after they left the company. 
What policies govern this?"

"The company wants to switch to a new email provider. What data protection 
and migration policies apply?"
```

---

## Category 9: Custom Questions

### Create Your Own
Try questions specific to your documents:
- **About your company**: "What is our policy on [topic]?"
- **About processes**: "How do we [procedure]?"
- **About compliance**: "What are we required to do regarding [requirement]?"
- **About relationships**: "How do [policy A] and [policy B] work together?"
- **About decisions**: "Under what conditions should we [decision]?"

---

## How the System Answers

When you ask a question, here's what happens:

1. **Orchestrator Agent** breaks down your question into subtasks
2. **Retriever Agent** searches for relevant documents and sections
3. **Analyzer Agent** synthesizes information across multiple documents
4. **Verifier Agent** checks that answers are grounded and accurate
5. **Memory Agent** tracks context for follow-up questions

The system then provides:
- ✓ A comprehensive answer
- ✓ Source documents cited
- ✓ Grounding verification (is it supported by documents?)
- ✓ Confidence level
- ✓ Execution trace showing how it reasoned

---

## Performance Tips

### Get Better Answers
- **Be specific**: "What is the process for expense reports?" vs "Tell me about expenses"
- **Reference documents**: "Based on the employee handbook, what..."
- **Ask for synthesis**: "How do security and productivity balance in remote work policy?"
- **Follow up**: Ask "Why?" or "Can you explain that more?" for deeper reasoning

### Observe System Behavior
- Watch how the system retrieves relevant documents
- Notice the grounding score (0-1, higher is better)
- Check the confidence level (low/medium/high)
- Review which documents are cited as sources

---

## Testing Tips

### Test Coverage
1. **Test factual retrieval**: Ask straightforward questions
2. **Test reasoning**: Ask questions requiring synthesis
3. **Test edge cases**: Ask about conflicting policies
4. **Test follow-ups**: Ask clarifying questions about answers
5. **Test hallucination detection**: Ask about things not in documents

### Debugging
- If grounding score is low (<0.5): The answer may not be well-supported
- If confidence is "low": The system is unsure; ask a follow-up
- If sources are empty: No documents were retrieved; try different keywords
- If answer is vague: Try a more specific question

---

## Expected Response Quality

### High Quality Answers ✓
- Directly answers your question
- Cites specific documents
- Grounding score > 0.6
- Confidence level: high or medium
- Multiple supporting details

### Medium Quality Answers ✓
- Answers the question with some details
- Cites documents
- Grounding score 0.4-0.6
- Confidence level: medium
- May be missing context

### Low Quality Answers ⚠
- Partial or indirect answer
- Minimal citations
- Grounding score < 0.4
- Confidence level: low
- Recommendation: Rephrase or follow up

---

## Pro Tips

### Phrase Questions Well
```
GOOD:  "What are the key security requirements for accessing customer data?"
LESS:  "Tell me about security and data"

GOOD:  "How should employees report a policy violation?"
LESS:  "What's the process?"

GOOD:  "What happens if an employee violates the confidentiality agreement?"
LESS:  "What about violations?"
```

### Chain Questions
```
Q1: "What is our remote work policy?"
Q2: "Can employees in [country] use this policy?"
Q3: "What equipment or allowances are provided?"
Q4: "How is productivity monitored for remote workers?"
```

### Challenge the System
```
Q: "What if two policies conflict? For example, X says [thing] but Y says [other thing]?"
Q: "Is there an exception to this policy mentioned anywhere?"
Q: "What exactly does '[term]' mean in this context?"
```

---

## Next Step

Ready to try?

```powershell
cd C:\repos\ai-engineering-lead
python main.py
```

Then copy-paste any question from above, or ask your own!

The system will show you:
- Answer
- Source documents
- Grounding score
- Confidence level
- Processing time

**Have fun exploring your knowledge base!**
