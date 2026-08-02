from newsfeed.keywords import matcher

KW = ["AI", "LLM", "fine-tun*", "machine learning"]


def test_matches_word_boundary():
    m = matcher(KW)
    assert m("New AI model released")
    assert m("Scaling LLMs is hard")
    assert not m("Airline stocks tumble")
    assert not m("Ferrari unveils new car")
    assert m("A machine learning approach")


def test_prefix_keywords():
    m = matcher(KW)
    assert m("Fine-tuning Llama at home")
    assert m("fine-tuned models")


def test_case_insensitive():
    m = matcher(KW)
    assert m("ai is eating software")
