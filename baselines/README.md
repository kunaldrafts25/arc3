# Official baseline provenance

starter_agent.py is the unchanged agent/my_agent.py from official starter commit
eeb1535404f321d280a8f9194bbc1d7aca5f05fc. Its text was compared against git show
after newline normalization. It preserves the original time seeding and ls20 bias.
The benchmark resets its RNG after construction and applies a strict equal action
cap for fair reproducible comparisons. Its action policy is unchanged.

Source: https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter
