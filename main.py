"""Main application entry point for the Enterprise Knowledge Operations Agent."""

import asyncio
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

from core.document_manager import DocumentManager
from core.orchestration import EnterpriseKnowledgeAgent


async def main():
    """Main application execution."""
    logger.info("Starting Enterprise Knowledge Operations Agent...")
    
    # Initialize the system
    doc_manager = DocumentManager()
    agent = EnterpriseKnowledgeAgent(doc_manager)
    
    logger.info(f"System initialized: {agent.get_system_status()}")
    
    # Load sample documents
    await setup_sample_documents(agent, doc_manager)
    
    # Interactive query loop
    await run_interactive_loop(agent)


async def setup_sample_documents(agent: EnterpriseKnowledgeAgent, 
                                 doc_manager: DocumentManager) -> None:
    """Set up sample documents for demonstration."""
    logger.info("Setting up sample documents...")
    
    # Sample Policy Document
    policy_doc = """
    COMPANY DATA PROTECTION POLICY
    
    1. Overview
    This policy establishes guidelines for handling, storing, and protecting company data
    across all departments and subsidiaries.
    
    2. Data Classification
    Data is classified into four levels:
    - Public: Information that can be shared openly
    - Internal: Information for internal use only
    - Confidential: Sensitive business information
    - Restricted: Highly sensitive information requiring special access controls
    
    3. Access Control
    - All access to confidential data requires manager approval
    - Multi-factor authentication is mandatory for sensitive systems
    - Access logs must be reviewed quarterly
    
    4. Encryption Requirements
    - Data at rest must be encrypted using AES-256
    - Data in transit must use TLS 1.2 or higher
    - Encryption keys must be stored separately from data
    
    5. Incident Response
    - Data breaches must be reported within 24 hours
    - Affected parties must be notified within 72 hours
    - Post-incident reviews are mandatory for all breaches
    """
    
    # Sample SOP Document
    sop_doc = """
    STANDARD OPERATING PROCEDURE: EMPLOYEE ONBOARDING
    
    1. Pre-Arrival
    - Prepare workspace and equipment
    - Set up email and system accounts
    - Create organizational email distribution lists
    
    2. First Day Orientation
    - Welcome meeting with direct manager
    - Office tour and facilities orientation
    - Introduction to team members
    - Review of company policies
    
    3. Systems Access
    - IT will provide credentials and access rights
    - Employee must change default password
    - Two-factor authentication setup is required
    
    4. Training Requirements
    - Mandatory: Data Protection and Security
    - Mandatory: Anti-harassment and Discrimination
    - Mandatory: Code of Conduct
    - Department-specific training within 30 days
    
    5. 30-Day Checklist
    - Complete all onboarding training
    - Meet with department heads
    - Set initial performance goals with manager
    - Submit completed tax forms
    
    6. 90-Day Review
    - Manager provides formal feedback
    - Employee provides feedback on onboarding
    - Performance goals are revisited
    """
    
    # Sample Contract Terms Document
    contract_doc = """
    SERVICE AGREEMENT - KEY TERMS AND CONDITIONS
    
    1. Service Scope
    The vendor agrees to provide the following services:
    - 24/7 technical support
    - System monitoring and maintenance
    - Security updates and patches
    - Monthly reporting on performance metrics
    
    2. Service Level Agreement (SLA)
    - System uptime: 99.9% guaranteed
    - Average response time: < 15 minutes
    - Critical incident resolution: < 4 hours
    - Scheduled maintenance windows: 2 hours per month maximum
    
    3. Confidentiality
    - All shared information is considered confidential
    - Information may not be shared with third parties without consent
    - Confidentiality obligations survive contract termination for 3 years
    
    4. Payment Terms
    - Monthly subscription: $50,000
    - Invoices due within 30 days
    - Late payments incur 1.5% monthly interest
    - Annual increase of 3% effective each January
    
    5. Term and Termination
    - Initial term: 3 years
    - Automatic renewal unless 90-day notice given
    - Either party may terminate for material breach with 30-day cure period
    
    6. Liability
    - Vendor liability limited to 12 months of fees
    - Neither party liable for indirect or consequential damages
    - Exception: liability for confidentiality breaches is unlimited
    """
    
    # Ingest documents
    try:
        agent.ingest_text(policy_doc, "Data Protection Policy")
        agent.ingest_text(sop_doc, "Employee Onboarding SOP")
        agent.ingest_text(contract_doc, "Service Agreement Terms")
        logger.info("Sample documents ingested successfully")
    except Exception as e:
        logger.error(f"Error ingesting documents: {e}")
    
    # Persist to disk
    doc_manager.persist()


async def run_interactive_loop(agent: EnterpriseKnowledgeAgent) -> None:
    """Run interactive query loop."""
    logger.info("\nStarting interactive query mode...")
    logger.info("Type 'exit' to quit, 'status' for system status\n")
    
    while True:
        try:
            query = input("\n❓ Enter your query: ").strip()
            
            if query.lower() == 'exit':
                logger.info("Exiting...")
                break
            elif query.lower() == 'status':
                status = agent.get_system_status()
                print(f"\n📊 System Status:")
                print(f"  - Agents: {status['agents_registered']}")
                print(f"  - Documents Loaded: {status['documents_loaded']}")
                print(f"  - Evaluations: {status['evaluations_performed']}")
                continue
            elif not query:
                continue
            
            # Process query
            logger.info(f"Processing query: {query}")
            response = await agent.process_query(query, top_k=3)
            
            # Display formatted response
            formatted = agent.format_response(response)
            print(formatted)
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            break
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            print(f"\n❌ Error: {e}")


def run_demo():
    """Run a demonstration with predefined queries."""
    logger.info("Running demonstration mode...")
    
    async def demo():
        doc_manager = DocumentManager()
        agent = EnterpriseKnowledgeAgent(doc_manager)
        
        # Setup sample documents
        await setup_sample_documents(agent, doc_manager)
        
        # Run sample queries
        sample_queries = [
            "What are the data protection requirements in our policy?",
            "What are the steps for employee onboarding in the first 30 days?",
            "What is the SLA for system uptime in our service agreement?"
        ]
        
        for query in sample_queries:
            logger.info(f"\nProcessing: {query}")
            response = await agent.process_query(query, top_k=3)
            print(agent.format_response(response))
    
    asyncio.run(demo())


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        run_demo()
    else:
        # Run interactive mode
        asyncio.run(main())
