from licenseflow_ai.rag.semantic_retriever import semantic_search


def test_discount_policy_retrieval():
    results = semantic_search(
        "Who should approve a fifteen percent discount?"
    )

    sources = [
        result["source"]
        for result in results
    ]

    assert "discount_approval_policy.md" in sources


def test_automotive_legal_policy_retrieval():
    results = semantic_search(
        "Does a car-related licensing deal require legal review?"
    )

    sources = [
        result["source"]
        for result in results
    ]

    assert (
        "legal_playbook.md" in sources
        or "licensing_policy.md" in sources
    )