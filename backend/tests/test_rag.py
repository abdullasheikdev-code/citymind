import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag import chunk_text, KeywordIndex, answer_from_context

SAMPLE_DOC = """
Section 4.2: Road Closure Approval Process. Any arterial road closure exceeding
48 hours requires approval from the Traffic Management Board. Emergency
services access must be preserved at all times during planned closures.

Section 7.1: Hospital Site Selection Guidelines. New hospital facilities
should be sited to minimize average ambulance response time across the
service area. Population density within a 2km radius should exceed 10,000
residents to justify a new facility.

Section 9.3: Flood Zone Building Restrictions. No new critical infrastructure
may be constructed within designated 100-year flood zones without elevated
foundation requirements.
"""


class TestChunking(unittest.TestCase):
    def test_chunk_text_covers_full_document(self):
        chunks = chunk_text(SAMPLE_DOC, chunk_size=300, overlap=50)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(c) > 0 for c in chunks))

    def test_empty_text_returns_no_chunks(self):
        self.assertEqual(chunk_text(""), [])


class TestKeywordIndex(unittest.TestCase):
    def setUp(self):
        self.index = KeywordIndex()
        for i, chunk in enumerate(chunk_text(SAMPLE_DOC, chunk_size=300, overlap=50)):
            self.index.add_chunk(document_id=1, chunk_index=i, content=chunk)

    def test_retrieves_hospital_section_for_hospital_query(self):
        results = self.index.retrieve("hospital site selection requirements", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertIn("Hospital Site Selection", results[0]["content"])

    def test_retrieves_road_closure_section_for_closure_query(self):
        results = self.index.retrieve("road closure approval process", top_k=1)
        self.assertIn("Road Closure Approval", results[0]["content"])

    def test_retrieves_flood_section_despite_word_form_mismatch(self):
        results = self.index.retrieve("flood zone construction rules", top_k=1)
        content_lower = results[0]["content"].lower()
        self.assertTrue("flood" in content_lower or "constructed" in content_lower)

    def test_irrelevant_query_returns_nothing_or_low_relevance(self):
        results = self.index.retrieve("quantum physics unrelated nonsense", top_k=3)
        self.assertEqual(len(results), 0)

    def test_answer_from_context_cites_sources(self):
        results = self.index.retrieve("hospital site selection", top_k=1)
        payload = answer_from_context("hospital site selection", results)
        self.assertEqual(len(payload["sources"]), 1)
        self.assertIn("document_id", payload["sources"][0])

    def test_answer_from_context_empty_when_nothing_found(self):
        payload = answer_from_context("nonsense query xyz123", [])
        self.assertEqual(payload["sources"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)