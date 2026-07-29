from taxtreat.engine.extractors import dividend_rule

sample = """
The tax charged shall not exceed 5% if the beneficial owner
holds at least 10% of the capital.

Otherwise the tax shall not exceed 15%.
"""

print(dividend_rule(sample))
