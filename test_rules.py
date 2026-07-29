from taxtreat.rules.dividends import extract_dividend_rule

sample = """
The tax charged shall not exceed 5% if the beneficial owner
holds at least 10% of the capital for at least 365 days.
Otherwise, the tax shall not exceed 15%.
"""

print(extract_dividend_rule(sample))
