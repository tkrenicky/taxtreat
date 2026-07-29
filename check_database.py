import sqlite3

conn = sqlite3.connect("taxtreat.db")
cur = conn.cursor()

tables = [
    "countries",
    "treaties",
    "treaty_versions",
    "articles",
    "paragraphs",
]

print("DATABASE SUMMARY")
print("=" * 40)

for table in tables:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    print(f"{table:20} {count}")

print("=" * 40)

print("\nFirst 10 articles:\n")

cur.execute("""
SELECT article_number, title
FROM articles
ORDER BY article_number
LIMIT 10
""")

for number, title in cur.fetchall():
    print(f"{number:>2}  {title}")

conn.close()
