import sys
try:
    import langchain
    print(f"LangChain Version: {langchain.__version__}")
    print(f"LangChain Path: {langchain.__file__}")
    
    import langchain.chains
    print("✅ langchain.chains found")
    
    from langchain.chains import RetrievalQA
    print("✅ RetrievalQA found")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print("Path:", sys.path)
