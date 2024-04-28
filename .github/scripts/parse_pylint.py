import sys


def main(lines):
    lines = lines.split("\n")

    summary = [line for line in lines if line.startswith(
        "Your code has been rated at")][0]

    report_start_index = [i for i, line in enumerate(
        lines) if line.startswith("Raw metrics")][0]
    report_end_index = [i for i, line in enumerate(
        lines) if line.startswith("Your code has been rated at")][0]

    report = lines[report_start_index:report_end_index-2]

    print(summary)
    print()
    print("<details>")
    print("  <summary>Full report</summary>")
    print()
    for line in report:
        print("  ", line)
    print()
    print("</details>")


if __name__ == "__main__":
    main(*sys.argv[1:])
