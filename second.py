def parse_table_counts(file_path):
    """
    Parses lines like:
    dbo.Users                                | 1245
    Returns: dict { "dbo.Users": 1245 }
    If count is not an int (error text), it will store None.
    """
    data = {}

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Skip headers/separators
            if not line or line.startswith(("Database:", "=", "-", "Schema.Table")):
                continue

            if "|" not in line:
                continue

            left, right = line.split("|", 1)
            table_name = left.strip()
            count_str = right.strip()

            # Try to convert count to int
            try:
                count_val = int(count_str)
            except Exception:
                count_val = None  # e.g., "ERROR: ..." or non-numeric

            data[table_name] = count_val

    return data


# =====================
# Input files
# =====================
file1 = "اولیه.txt"  # Replace with actual file name
file2 = "ثبت درخواست خروج_2.txt"  # Replace with actual file name
file3 = "خروج از انبار_3.txt"  # Replace with actual file name
file4 = "database_tables_record_count_4.txt"  # Replace with actual file name
d1 = parse_table_counts(file3)
d2 = parse_table_counts(file4)

tables1 = set(d1.keys())
tables2 = set(d2.keys())

missing_in_2 = sorted(tables1 - tables2)
missing_in_1 = sorted(tables2 - tables1)

common = sorted(tables1 & tables2)

# Find tables with different counts (including None vs int)
diff = []
for t in common:
    if d1.get(t) != d2.get(t):
        diff.append((t, d1.get(t), d2.get(t)))

# Sort by biggest absolute difference (when both are ints), otherwise keep last
def sort_key(item):
    _, a, b = item
    if isinstance(a, int) and isinstance(b, int):
        return (-abs(a - b), item[0])
    return (10**18, item[0])  # push non-int comparisons to the end

diff.sort(key=sort_key)

# =====================
# Output
# =====================
print("✅ Tables with DIFFERENT record counts:\n")
for t, c1, c2 in diff:
    print(f"- {t}: file1={c1} | file2={c2}")

print("\n--- Summary ---")
print(f"File1 tables: {len(tables1)}")
print(f"File2 tables: {len(tables2)}")
print(f"Common tables: {len(common)}")
print(f"Different counts: {len(diff)}")

if missing_in_2:
    print("\n⚠️ Tables present in file1 but missing in file2:")
    for t in missing_in_2:
        print("  -", t)

if missing_in_1:
    print("\n⚠️ Tables present in file2 but missing in file1:")
    for t in missing_in_1:
        print("  -", t)
