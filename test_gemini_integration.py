#!/usr/bin/env python3
"""
Gemini Integration Test Script

This script demonstrates the Gemini LLM integration in the Enterprise Knowledge Agent.
It tests:
1. Analyzer Agent initialization (with/without Gemini)
2. Fallback mechanism
3. Full pipeline with mock documents
"""

import os
import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from agents.analyzer_agent import AnalyzerAgent
from core.types import RetrievalResult


async def test_gemini_initialization():
    """Test 1: Verify Gemini agent initialization"""
    print("\n" + "="*70)
    print("TEST 1: Gemini Agent Initialization")
    print("="*70)
    
    try:
        agent = AnalyzerAgent()
        
        if agent.llm is not None:
            print("[SUCCESS] Gemini LLM initialized!")
            print(f"    Model: {agent.llm.model_name}")
            print(f"    Temperature: {agent.llm.temperature}")
            print(f"    Max tokens: {agent.llm.max_output_tokens}")
            return True
        else:
            print("[INFO] Gemini not initialized (no API key)")
            print("    System will use template-based synthesis")
            print("    To use Gemini:")
            print("    1. Get API key from https://ai.google.dev/")
            print("    2. Add GOOGLE_API_KEY=... to .env")
            print("    3. Restart the system")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to initialize Gemini: {e}")
        return False


async def test_synthesis_with_documents():
    """Test 2: Test answer synthesis with sample documents"""
    print("\n" + "="*70)
    print("TEST 2: Answer Synthesis (Document Retrieval Simulation)")
    print("="*70)
    
    try:
        agent = AnalyzerAgent()
        
        # Create sample retrieval results (simulating document retrieval)
        sample_results = [
            RetrievalResult(
                document_id="doc_001",
                source="Employee Handbook v2024",
                content="Work hours are 9am to 5pm Monday through Friday. Employees can work remotely up to 2 days per week with manager approval.",
                relevance_score=0.95,
                chunk_id="ch_001",
                metadata={
                    "title": "Employee Handbook - Work Hours",
                    "section": "1.2",
                    "page": 5
                }
            ),
            RetrievalResult(
                document_id="doc_002",
                source="HR Policies",
                content="All full-time employees receive 20 days of paid vacation annually. Holiday schedules are published each year.",
                relevance_score=0.87,
                chunk_id="ch_002",
                metadata={
                    "title": "HR Policies - Time Off",
                    "section": "3.1",
                    "page": 12
                }
            ),
            RetrievalResult(
                document_id="doc_003",
                source="Remote Work Guidelines",
                content="Remote work is available for most roles. Employees must maintain core hours 10am-3pm EST and have reliable internet.",
                relevance_score=0.82,
                chunk_id="ch_003",
                metadata={
                    "title": "Remote Work Guidelines",
                    "section": "2.0",
                    "page": 8
                }
            )
        ]
        
        # Test synthesis
        query = "What are the work hour policies and vacation benefits?"
        
        print(f"\nQuery: {query}")
        print(f"Documents: {len(sample_results)}")
        
        reasoning_steps = await agent._generate_reasoning_steps(query, sample_results)
        print(f"\nReasoning Steps ({len(reasoning_steps)}):")
        for i, step in enumerate(reasoning_steps, 1):
            print(f"  {i}. {step}")
        
        answer = await agent._synthesize_answer(query, sample_results, reasoning_steps)
        
        llm_status = "Using Gemini LLM" if agent.llm else "Using Template Synthesis"
        print(f"\n{llm_status}:")
        print("-" * 70)
        print(answer)
        print("-" * 70)
        
        source_refs = agent._extract_source_references(sample_results)
        print(f"\nSources ({len(source_refs)}):")
        for i, ref in enumerate(source_refs, 1):
            print(f"  {i}. {ref['title']} (Relevance: {ref['relevance_score']:.2f})")
        
        return True
    except Exception as e:
        print(f"[ERROR] Synthesis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration_status():
    """Test 3: Overall integration status"""
    print("\n" + "="*70)
    print("TEST 3: Integration Status Report")
    print("="*70)
    
    try:
        agent = AnalyzerAgent()
        
        gemini_status = "ENABLED" if agent.llm else "DISABLED (template fallback)"
        
        print("\n[Integration Status]")
        print(f"  Gemini LLM: {gemini_status}")
        print(f"  Agent Role: {agent.role}")
        print(f"  Agent ID: {agent.agent_id}")
        print(f"  Status: {agent.status}")
        
        print("\n[Configuration]")
        from config.settings import GEMINI_ENABLED, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS
        print(f"  GEMINI_ENABLED: {GEMINI_ENABLED}")
        print(f"  GEMINI_MODEL: {GEMINI_MODEL}")
        print(f"  GEMINI_TEMPERATURE: {GEMINI_TEMPERATURE}")
        print(f"  GEMINI_MAX_TOKENS: {GEMINI_MAX_TOKENS}")
        
        print("\n[Dependencies]")
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            print("  [OK] langchain-google-genai: INSTALLED")
        except ImportError:
            print("  [MISSING] langchain-google-genai: NOT INSTALLED")
        
        try:
            import google.generativeai
            print("  [OK] google-generativeai: INSTALLED")
        except ImportError:
            print("  [MISSING] google-generativeai: NOT INSTALLED")
        
        print("\n[API Key Status]")
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key:
            key_preview = api_key[:10] + "..."
            print(f"  [OK] GOOGLE_API_KEY: SET ({key_preview})")
        else:
            print(f"  [MISSING] GOOGLE_API_KEY: NOT SET")
            print("    Add to .env file: GOOGLE_API_KEY=your-key-here")
        
        print("\n[Documentation]")
        docs = [
            "README.md",
            "GEMINI_SETUP_GUIDE.md",
            "LLM_INTEGRATION_UPDATE.md",
            "docs/ARCHITECTURE.md"
        ]
        for doc in docs:
            if Path(doc).exists():
                print(f"  [OK] {doc}")
            else:
                print(f"  [MISSING] {doc}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Status check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("ENTERPRISE KNOWLEDGE AGENT - GEMINI INTEGRATION TEST")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Gemini Initialization", await test_gemini_initialization()))
    results.append(("Answer Synthesis", await test_synthesis_with_documents()))
    results.append(("Integration Status", await test_integration_status()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! System is ready with Gemini integration.")
    else:
        print("\n[WARNING] Some tests failed. Check logs above for details.")
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    
    if not results[0][1]:  # Gemini not initialized
        print("""
1. Get your FREE Google API key:
   - Visit: https://ai.google.dev/
   - Click: Get API Key
   - Create project (if needed)
   - Copy your key

2. Add to .env file:
   GOOGLE_API_KEY=your-key-here

3. Restart and test again:
   python test_gemini_integration.py

4. Run the full application:
   python main.py
        """)
    else:
        print("""
Your system is ready! To use the Gemini-powered agent:

1. Run the application:
   python main.py

2. Or run the demo:
   python demo_app.py

3. Check documentation:
   - GEMINI_SETUP_GUIDE.md
   - LLM_INTEGRATION_UPDATE.md
   - README.md

Questions? See docs/ directory for complete guides.
        """)
    
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())


async def test_synthesis_with_documents():
    """Test 2: Test answer synthesis with sample documents"""
    print("\n" + "="*70)
    print("TEST 2: Answer Synthesis (Document Retrieval Simulation)")
    print("="*70)
    
    try:
        agent = AnalyzerAgent()
        
        # Create sample retrieval results (simulating document retrieval)
        sample_results = [
            RetrievalResult(
                source="Employee Handbook v2024",
                content="Work hours are 9am to 5pm Monday through Friday. Employees can work remotely up to 2 days per week with manager approval.",
                relevance_score=0.95,
                chunk_id="ch_001",
                metadata={
                    "title": "Employee Handbook - Work Hours",
                    "section": "1.2",
                    "page": 5
                }
            ),
            RetrievalResult(
                source="HR Policies",
                content="All full-time employees receive 20 days of paid vacation annually. Holiday schedules are published each year.",
                relevance_score=0.87,
                chunk_id="ch_002",
                metadata={
                    "title": "HR Policies - Time Off",
                    "section": "3.1",
                    "page": 12
                }
            ),
            RetrievalResult(
                source="Remote Work Guidelines",
                content="Remote work is available for most roles. Employees must maintain core hours 10am-3pm EST and have reliable internet.",
                relevance_score=0.82,
                chunk_id="ch_003",
                metadata={
                    "title": "Remote Work Guidelines",
                    "section": "2.0",
                    "page": 8
                }
            )
        ]
        
        # Test synthesis
        query = "What are the work hour policies and vacation benefits?"
        
        print(f"\nQuery: {query}")
        print(f"Documents: {len(sample_results)}")
        
        reasoning_steps = await agent._generate_reasoning_steps(query, sample_results)
        print(f"\nReasoning Steps ({len(reasoning_steps)}):")
        for i, step in enumerate(reasoning_steps, 1):
            print(f"  {i}. {step}")
        
        answer = await agent._synthesize_answer(query, sample_results, reasoning_steps)
        
        print(f"\n{'Using Gemini LLM' if agent.llm else 'Using Template Synthesis'}:")
        print("-" * 70)
        print(answer)
        print("-" * 70)
        
        source_refs = agent._extract_source_references(sample_results)
        print(f"\nSources ({len(source_refs)}):")
        for i, ref in enumerate(source_refs, 1):
            print(f"  {i}. {ref['title']} (Relevance: {ref['relevance_score']:.2f})")
        
        return True
    except Exception as e:
        print(f"[-] ERROR: Synthesis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration_status():
    """Test 3: Overall integration status"""
    print("\n" + "="*70)
    print("TEST 3: Integration Status Report")
    print("="*70)
    
    try:
        agent = AnalyzerAgent()
        
        print("\n[Integration Status]")
        print(f"  Gemini LLM: {'✓ ENABLED' if agent.llm else '✗ DISABLED (template fallback active)'}")
        print(f"  Agent Role: {agent.role}")
        print(f"  Agent ID: {agent.agent_id}")
        print(f"  Status: {agent.status}")
        
        print("\n[Configuration]")
        from config.settings import GEMINI_ENABLED, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS
        print(f"  GEMINI_ENABLED: {GEMINI_ENABLED}")
        print(f"  GEMINI_MODEL: {GEMINI_MODEL}")
        print(f"  GEMINI_TEMPERATURE: {GEMINI_TEMPERATURE}")
        print(f"  GEMINI_MAX_TOKENS: {GEMINI_MAX_TOKENS}")
        
        print("\n[Dependencies]")
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            print("  ✓ langchain-google-genai: INSTALLED")
        except ImportError:
            print("  ✗ langchain-google-genai: NOT INSTALLED")
        
        try:
            import google.generativeai
            print("  ✓ google-generativeai: INSTALLED")
        except ImportError:
            print("  ✗ google-generativeai: NOT INSTALLED")
        
        print("\n[API Key Status]")
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key:
            print(f"  ✓ GOOGLE_API_KEY: SET ({api_key[:10]}...)")
        else:
            print(f"  ✗ GOOGLE_API_KEY: NOT SET")
            print("    Add to .env file: GOOGLE_API_KEY=your-key-here")
        
        print("\n[Documentation]")
        docs = [
            "README.md",
            "GEMINI_SETUP_GUIDE.md",
            "LLM_INTEGRATION_UPDATE.md",
            "docs/ARCHITECTURE.md"
        ]
        for doc in docs:
            if Path(doc).exists():
                print(f"  ✓ {doc}")
            else:
                print(f"  ✗ {doc}")
        
        return True
    except Exception as e:
        print(f"[-] ERROR: Status check failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("ENTERPRISE KNOWLEDGE AGENT - GEMINI INTEGRATION TEST")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Gemini Initialization", await test_gemini_initialization()))
    results.append(("Answer Synthesis", await test_synthesis_with_documents()))
    results.append(("Integration Status", await test_integration_status()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[✓ PASS]" if result else "[✗ FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[✓] All tests passed! System is ready with Gemini integration.")
    else:
        print("\n[!] Some tests failed. Check logs above for details.")
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    
    if not results[0][1]:  # Gemini not initialized
        print("""
1. Get your FREE Google API key:
   - Visit: https://ai.google.dev/
   - Click: Get API Key
   - Create project (if needed)
   - Copy your key

2. Add to .env file:
   GOOGLE_API_KEY=your-key-here

3. Restart and test again:
   python test_gemini_integration.py

4. Run the full application:
   python main.py
        """)
    else:
        print("""
Your system is ready! To use the Gemini-powered agent:

1. Run the application:
   python main.py

2. Or run the demo:
   python demo_app.py

3. Check documentation:
   - GEMINI_SETUP_GUIDE.md
   - LLM_INTEGRATION_UPDATE.md
   - README.md

Questions? See docs/ directory for complete guides.
        """)
    
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
