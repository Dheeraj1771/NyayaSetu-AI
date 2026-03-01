#!/usr/bin/env python3
"""
Validation script to check RAG pipeline setup
"""

import sys
from pathlib import Path


def check_dependencies():
    """Check if required packages are installed"""
    print("Checking dependencies...")
    
    required = {
        'boto3': 'AWS Bedrock integration',
        'sentence_transformers': 'Embedding generation',
        'numpy': 'Similarity calculations',
        'PyPDF2': 'PDF processing'
    }
    
    missing = []
    for package, purpose in required.items():
        try:
            __import__(package)
            print(f"  ✓ {package} - {purpose}")
        except ImportError:
            print(f"  ✗ {package} - {purpose} (MISSING)")
            missing.append(package)
    
    return len(missing) == 0, missing


def check_knowledge_base():
    """Check if knowledge base exists"""
    print("\nChecking knowledge base...")
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    kb_path = project_root / "knowledge_base" / "knowledge_base.json"
    
    if kb_path.exists():
        import json
        with open(kb_path, 'r') as f:
            kb = json.load(f)
        print(f"  ✓ Knowledge base found: {len(kb)} chunks")
        return True
    else:
        print(f"  ✗ Knowledge base not found at: {kb_path}")
        print(f"     Run: python3 rag_kb_setup.py")
        return False


def check_aws_credentials():
    """Check if AWS credentials are configured"""
    print("\nChecking AWS credentials...")
    
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"  ✓ AWS credentials configured")
        print(f"     Account: {identity['Account']}")
        print(f"     User: {identity['Arn'].split('/')[-1]}")
        return True
    except Exception as e:
        print(f"  ✗ AWS credentials not configured")
        print(f"     Error: {e}")
        print(f"     Run: aws configure")
        return False


def check_bedrock_access():
    """Check if Bedrock is accessible"""
    print("\nChecking Bedrock access...")
    
    try:
        import boto3
        bedrock = boto3.client('bedrock-runtime', region_name='ap-south-1')
        print(f"  ✓ Bedrock Runtime client initialized")
        print(f"     Region: ap-south-1 (Mumbai)")
        return True
    except Exception as e:
        print(f"  ✗ Bedrock access failed")
        print(f"     Error: {e}")
        return False


def main():
    """Run all validation checks"""
    print("=" * 70)
    print("NyayaSetu AI - RAG Pipeline Validation")
    print("=" * 70)
    
    checks = []
    
    # Check dependencies
    deps_ok, missing = check_dependencies()
    checks.append(("Dependencies", deps_ok))
    
    # Check knowledge base
    kb_ok = check_knowledge_base()
    checks.append(("Knowledge Base", kb_ok))
    
    # Check AWS credentials
    aws_ok = check_aws_credentials()
    checks.append(("AWS Credentials", aws_ok))
    
    # Check Bedrock access
    if aws_ok:
        bedrock_ok = check_bedrock_access()
        checks.append(("Bedrock Access", bedrock_ok))
    else:
        checks.append(("Bedrock Access", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for check_name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} - {check_name}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n✓ All checks passed! RAG pipeline is ready.")
        print("\nNext steps:")
        print("  1. Run: python3 query_single.py \"What is a consumer?\"")
        print("  2. Or:  python3 test_rag_query.py")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        
        if not deps_ok:
            print("\nInstall missing dependencies:")
            print("  pip install -r ../../requirements.txt")
        
        if not kb_ok:
            print("\nBuild knowledge base:")
            print("  python3 rag_kb_setup.py")
        
        if not aws_ok:
            print("\nConfigure AWS credentials:")
            print("  aws configure")
            print("  See: docs/BEDROCK_SETUP.md")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
