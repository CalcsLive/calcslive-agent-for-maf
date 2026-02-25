# test_excel_api.py
# Manual test script for Excel COM automation
# Run with: python test_excel_api.py

import sys
from excel_api import (
    get_health,
    read_range,
    write_cell,
    read_pq_table,
)


def test_health():
    """Test Excel connection health."""
    print("=" * 50)
    print("Testing get_health()...")
    result = get_health()
    print(f"Result: {result}")

    if result.get("success"):
        print(f"[OK] Excel connected: {result.get('workbookName')}")
        print(f"     Active sheet: {result.get('sheetName')}")
    else:
        print(f"[FAIL] {result.get('error')}")
        print("       Make sure Excel is open with a workbook")

    return result.get("success")


def test_read_range():
    """Test reading a range from Excel."""
    print("=" * 50)
    print("Testing read_range('A1:E6')...")

    result = read_range("A1:E6")
    print(f"Result: {result}")

    if result.get("success"):
        print(f"[OK] Read {result.get('rowCount')} rows, {result.get('colCount')} cols")
        for i, row in enumerate(result.get("data", []), 1):
            print(f"     Row {i}: {row}")
    else:
        print(f"[FAIL] {result.get('error')}")

    return result.get("success")


def test_read_pq_table():
    """Test reading PQ table structure."""
    print("=" * 50)
    print("Testing read_pq_table()...")

    result = read_pq_table()
    print(f"Result: {result}")

    if result.get("success"):
        pqs = result.get("pqs", [])
        print(f"[OK] Found {len(pqs)} PQs")
        print(f"     Inputs: {result.get('inputCount')}, Outputs: {result.get('outputCount')}")
        print(f"     Columns: {result.get('columns')}")

        for pq in pqs:
            io_type = "INPUT" if pq.get("isInput") else "OUTPUT"
            print(f"     - {pq.get('sym')}: {pq.get('value')} {pq.get('unit')} [{io_type}]")
            if pq.get("expression"):
                print(f"         expr: {pq.get('expression')}")
    else:
        print(f"[FAIL] {result.get('error')}")
        if result.get("foundHeaders"):
            print(f"       Found headers: {result.get('foundHeaders')}")

    return result.get("success")


def test_write_cell():
    """Test writing to a cell (CAUTION: modifies spreadsheet)."""
    print("=" * 50)
    print("Testing write_cell('G1', 'Test Value')...")

    # Write to a safe cell (G1) to avoid overwriting data
    result = write_cell("G1", "Test Value")
    print(f"Result: {result}")

    if result.get("success"):
        print(f"[OK] Wrote to cell G1")
    else:
        print(f"[FAIL] {result.get('error')}")

    return result.get("success")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 50)
    print("CalcsLive Excel Bridge - Test Suite")
    print("=" * 50)
    print("\nMake sure Excel is open with the demo spreadsheet!")
    print("Expected format: Description | Symbol | Expression | Value | Unit")
    print()

    # Run tests
    health_ok = test_health()

    if not health_ok:
        print("\n[FAIL] Cannot proceed - Excel not connected")
        return False

    print()
    read_ok = test_read_range()

    print()
    pq_ok = test_read_pq_table()

    print()
    # Skip write test by default to avoid modifying spreadsheet
    # write_ok = test_write_cell()

    print()
    print("=" * 50)
    print("Test Summary:")
    print(f"  Health check:  {'OK' if health_ok else 'FAIL'}")
    print(f"  Read range:    {'OK' if read_ok else 'FAIL'}")
    print(f"  Read PQ table: {'OK' if pq_ok else 'FAIL'}")
    print("=" * 50)

    return health_ok and read_ok and pq_ok


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
