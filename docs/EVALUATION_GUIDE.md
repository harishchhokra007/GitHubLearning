# Evaluation & Guardrails Documentation

## Overview

This document describes the evaluation mechanisms, guardrails, and observability features of the Enterprise Knowledge Operations Agent system.

## Evaluation Framework

The system implements comprehensive evaluation across multiple dimensions:

### 1. Retrieval Evaluation

**Purpose**: Assess the quality and relevance of retrieved documents

**Metrics**:
- **Retrieval Relevance Score** (0-1): Average relevance of retrieved documents
  - Calculated from cosine similarity to query
  - Higher = more relevant documents selected

- **Number of Documents Retrieved**: Actual count of relevant documents found
  - Threshold-based filtering at 0.6 relevance minimum

- **Coverage**: Percentage of documents meeting relevance threshold
  - Indicates adequacy of retrieval

**Implementation**:
```python
# In evaluation_system.py
def _evaluate_retrieval_relevance(self, sources):
    if not sources:
        return 0.0
    relevance_scores = [s.relevance_score for s in sources]
    return sum(relevance_scores) / len(relevance_scores)
```

**Acceptable Range**: 0.65-1.0
**Warning Threshold**: < 0.5

---

### 2. Grounding Verification

**Purpose**: Ensure answers are supported by source documents

**Metrics**:
- **Grounding Score** (0-1): How well answer is grounded in sources
  - Document Reference Score (40%): % of sources referenced in answer
  - Average Relevance (60%): Quality of selected sources

- **Is Grounded**: Boolean flag indicating if score meets threshold (0.7)

**Calculation**:
```
Grounding Score = (doc_reference_score * 0.4) + (avg_relevance * 0.6)
```

**Implementation**:
```python
# In verifier_agent.py
async def _verify_grounding(self, answer, documents):
    referenced_docs = count_referenced_sources(answer, documents)
    doc_reference_score = referenced_docs / len(documents)
    avg_relevance = mean([d.relevance_score for d in documents])
    return (doc_reference_score * 0.4) + (avg_relevance * 0.6)
```

**Acceptable Range**: 0.7-1.0
**Warning Threshold**: < 0.6

---

### 3. Hallucination Detection

**Purpose**: Identify unsupported or fabricated claims in responses

**Techniques**:
- **Length Anomaly**: Answer significantly longer than source material
- **Unsupported Claims**: Assertions not present in retrieved documents
- **Attribution Check**: Whether sources are properly referenced

**Flags Triggered By**:
- Answer length > 2x source material length
- Claims with "according to" but unsupported by documents
- More than 2 unsupported statements

**Example**:
```python
# In verifier_agent.py
async def _detect_hallucinations(self, answer, documents):
    document_content = "\n".join([d.content for d in documents])
    
    if len(answer) > len(document_content) * 2:
        hallucinations.append("Answer significantly longer than source")
    
    # Check unsupported claims
    unsupported = count_unsupported_claims(answer, document_content)
    if unsupported > 0:
        hallucinations.append(f"Found {unsupported} unsupported claims")
    
    return hallucinations
```

**Severity Levels**:
- **Low**: 1 minor anomaly (length)
- **Medium**: 1 unsupported claim
- **High**: 2+ unsupported claims or critical hallucination

---

### 4. Confidence Level Assessment

**Purpose**: Overall quality confidence in generated response

**Determination Logic**:
```
IF grounding >= 0.8 AND hallucinations == 0:
    confidence = "high"
ELIF grounding >= 0.6 AND hallucinations <= 1:
    confidence = "medium"
ELSE:
    confidence = "low"
```

**Confidence Levels**:
- **High**: Response well-grounded, no hallucinations detected
- **Medium**: Acceptable grounding, minor potential issues
- **Low**: Low confidence, recommend verification

---

## Failure Detection

### Failure Categories

1. **Retrieval Failures**
   - No documents retrieved
   - All results below relevance threshold
   - Flag: "No documents retrieved" or "Low retrieval relevance: X"

2. **Grounding Failures**
   - Grounding score < threshold
   - Insufficient source attribution
   - Flag: "Low grounding score: X"

3. **Hallucination Failures**
   - Unsupported claims detected
   - Confidence contradictions
   - Flag: "Potential hallucinations detected: N"

4. **System Failures**
   - Processing errors
   - Agent execution failures
   - Flag: "System errors: N"

### Detection Implementation

```python
@staticmethod
def _detect_failures(response, retrieval_relevance, grounding_score):
    failures = []
    
    if len(response.sources) == 0:
        failures.append("No documents retrieved")
    elif retrieval_relevance < 0.5:
        failures.append(f"Low retrieval relevance: {retrieval_relevance:.2f}")
    
    if grounding_score < 0.6:
        failures.append(f"Low grounding score: {grounding_score:.2f}")
    
    if response.verification.potential_hallucinations:
        failures.append(f"Potential hallucinations: {len(...)}")
    
    if response.errors:
        failures.append(f"System errors: {len(response.errors)}")
    
    return failures
```

---

## Guardrails Implementation

### 1. Input Validation

**Rules**:
- Query must not be empty
- Query length: 1-1000 characters
- No special injection patterns

**Implementation**:
```python
if not query:
    raise ValueError("Query is required")
if len(query) > 1000:
    raise ValueError("Query too long")
```

### 2. Output Validation

**Rules**:
- Answer must reference at least one source
- Answer length must be reasonable
- Confidence must be assigned

**Implementation**:
```python
if not answer_sources:
    warnings.append("No sources referenced")
if len(answer) > 5000:
    warnings.append("Answer unusually long")
```

### 3. Source Attribution

**Requirements**:
- All factual claims must cite sources
- Sources must be ranked by relevance
- Source metadata must be preserved

**Implementation**:
```python
source_references = [
    {
        'source': r.source,
        'title': r.metadata.get('title'),
        'relevance_score': r.relevance_score
    }
    for r in retrieval_results
]
```

### 4. Confidence Thresholds

**Application**:
- Response only returned if confidence >= minimum threshold
- Low confidence triggers additional warnings
- Medium confidence recommends verification

**Configuration**:
```python
GROUNDING_THRESHOLD = 0.7      # Min grounding for acceptance
HALLUCINATION_THRESHOLD = 0.5  # Min confidence if hallucinations
```

---

## Observability & Logging

### Execution Traces

**Captured Information**:
- Agent ID and role
- Execution step name
- Timestamp
- Detailed metrics/results

**Example**:
```json
{
  "agent_id": "orchestrator_1",
  "step_name": "Query decomposed",
  "timestamp": "2026-10-03T12:00:00Z",
  "details": {
    "num_subtasks": 3,
    "query": "What is our policy?"
  }
}
```

### Agent Decision Traces

**Captured**:
- Agent role that made decision
- Decision type (retrieval, analysis, verification)
- Key parameters used
- Outcome

**Example**:
```json
{
  "agent_id": "retriever_1",
  "decision": "retrieve_documents",
  "parameters": {
    "query": "data protection",
    "top_k": 5
  },
  "outcome": {
    "num_results": 3,
    "avg_relevance": 0.82
  }
}
```

### Evaluation Logs

**File Format**: JSON (saved in `evaluation/eval_*.json`)

**Contents**:
- Response ID
- Query
- Evaluation timestamp
- All metrics
- Verification results
- Warnings and flags

**Example**:
```json
{
  "response_id": "resp_abc123",
  "query": "What is the data protection policy?",
  "metrics": {
    "retrieval_relevance": 0.85,
    "grounding_score": 0.82,
    "hallucination_detected": false,
    "failure_flags": [],
    "num_execution_steps": 12,
    "num_agent_decisions": 5
  },
  "verification": {
    "is_grounded": true,
    "confidence_level": "high",
    "warnings": []
  }
}
```

---

## Evaluation Workflow

### Processing Pipeline

```
Query Received
    ↓
Agent Execution
    ├─ Orchestrator: Plan decomposition
    ├─ Retriever: Document retrieval
    ├─ Analyzer: Synthesis
    └─ Verifier: Validation
    ↓
Evaluation System
    ├─ Retrieval relevance → Score
    ├─ Grounding verification → Score
    ├─ Hallucination detection → Flags
    ├─ Failure detection → Flags
    └─ Confidence assignment
    ↓
Report Generation
    ├─ JSON evaluation file
    ├─ Console log report
    └─ Warning compilation
    ↓
Response Delivered
```

---

## Sample Evaluation Report

```
================== EVALUATION REPORT ==================
Response ID: resp_abc123
Query: What is our data protection policy?
Timestamp: 2026-10-03T12:00:00Z

--- RETRIEVAL EVALUATION ---
Relevance Score: 0.85
Documents Retrieved: 3

--- GROUNDING EVALUATION ---
Grounding Score: 0.82
Is Grounded: True
Confidence Level: high

--- HALLUCINATION DETECTION ---
Hallucinations Detected: False
Count: 0

--- FAILURE DETECTION ---
Failure Flags: 0

--- WARNINGS ---
(None)

--- EXECUTION TRACE ---
Steps: 12
  1. orchestrator_1: Query decomposed into 3 subtasks
  2. retriever_1: Retrieved 3 documents (avg relevance: 0.85)
  3. analyzer_1: Synthesized answer from sources
  4. verifier_1: Verified grounding (score: 0.82)
  5. ...

========================================================
```

---

## Evaluation Metrics Summary Statistics

### System Level Metrics

After processing multiple queries, the system tracks:

```python
{
    'total_evaluations': 42,
    'avg_retrieval_relevance': 0.78,
    'avg_grounding_score': 0.81,
    'responses_with_hallucinations': 3,
    'total_failure_flags': 2,
    'success_rate': 92.9%  # Without hallucinations/failures
}
```

---

## Best Practices for Evaluation

### For System Administrators

1. **Monitor Evaluation Reports**
   - Check `evaluation/` directory for recent reports
   - Review failure flags and warnings
   - Track metrics over time

2. **Adjust Thresholds**
   - If false positives increase: lower thresholds
   - If false negatives increase: raise thresholds
   - Document changes in config

3. **Log Analysis**
   - Review `logs/app.log` for errors
   - Trace failed queries to root cause
   - Monitor execution times

### For System Users

1. **Interpret Confidence Levels**
   - High: Safe to use without verification
   - Medium: Recommend spot-checking sources
   - Low: Verify against original documents

2. **Review Warnings**
   - Always read warnings provided
   - Click through to source documents
   - Report hallucinations if detected

3. **Provide Feedback**
   - Flag incorrect answers
   - Suggest missing documents
   - Help improve system accuracy

---

## Customization Options

### Modify Evaluation Thresholds

Edit `config/settings.py`:
```python
GROUNDING_THRESHOLD = 0.7        # Adjust for strictness
HALLUCINATION_THRESHOLD = 0.5    # Adjust detection sensitivity
RETRIEVAL_SCORE_THRESHOLD = 0.6  # Adjust minimum relevance
```

### Add Custom Metrics

Extend `EvaluationSystem` class:
```python
class CustomEvaluationSystem(EvaluationSystem):
    def evaluate_custom_metric(self, response):
        # Your custom evaluation logic
        pass
```

### Integrate External Validators

```python
# In verifier_agent.py
async def _apply_external_validation(self, answer):
    # Call external fact-checking service
    result = await external_validator.check(answer)
    return result
```

---

## Troubleshooting

### Low Retrieval Relevance

**Symptoms**: Retrieval relevance < 0.5

**Causes**:
- Poor document quality or relevance
- Query too specific
- Documents not properly chunked

**Solutions**:
- Review document quality
- Try more general query
- Adjust chunk size

### Low Grounding Scores

**Symptoms**: Grounding score < 0.6, confidence drops

**Causes**:
- Answer doesn't reference sources
- Retrieved documents not actually relevant
- Analyzer not synthesizing well

**Solutions**:
- Improve analyzer logic
- Improve retrieval quality
- Check document relevance

### High Hallucination Flags

**Symptoms**: Frequent hallucination warnings

**Causes**:
- Analyzer generating unsupported claims
- Weak retrieval results
- Configuration too sensitive

**Solutions**:
- Improve analyzer model
- Add better documents
- Adjust thresholds

---

## Version History

- **v1.0** (Oct 2026): Initial evaluation framework
  - Basic grounding verification
  - Hallucination detection
  - Execution tracing
  - JSON evaluation reporting

---

**Last Updated**: October 2026
**Maintainer**: AI Engineering Lead Team
