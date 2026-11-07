"""Optional integration smoke tests; skipped if third-party stacks are not installed."""
import unittest
class OptionalIntegrationTests(unittest.TestCase):
 def test_crewai_import(self):
  try: import crewai
  except ImportError: self.skipTest('Install requirements.txt to test CrewAI')
  from agents.mock_llm import DeterministicMockLLM
  self.assertTrue(callable(DeterministicMockLLM().call))
 def test_chroma_import(self):
  try: import chromadb
  except ImportError: self.skipTest('Install requirements.txt to test ChromaDB')
  self.assertTrue(hasattr(chromadb,'PersistentClient'))
 def test_sentence_transformers_import(self):
  try: import sentence_transformers
  except ImportError: self.skipTest('Install requirements.txt to test SentenceTransformers')
 def test_autogen_import(self):
  try: import autogen_agentchat
  except ImportError: self.skipTest('Install requirements.txt to test AutoGen')
if __name__=='__main__': unittest.main()
