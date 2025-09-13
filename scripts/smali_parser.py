def get_smali_lines(file: str) -> list[str]:
    lines = []
    with open(file, "r", encoding="utf-8") as smali:
        lines = smali.readlines()
    return lines


def save_smali_lines(file: str, lines: list[str]) -> None:
    with open(file, "w", encoding="utf-8") as f:
        f.writelines(lines)


def find_smali_method_start(lines: list[str], index: int) -> int:
    while True:
        index -= 1
        if lines[index].find(".method") >= 0:
            return index


def find_smali_method_end(lines: list[str], index: int) -> int:
    while True:
        index += 1
        if lines[index].find(".end method") >= 0:
            return index


def debug_print_smali_method(lines: list[str], start: int, end: int) -> None:
    while start != (end + 1):
        print(start, lines[start])
        start += 1


def replace_smali_method_body(
    lines: list[str], start: int, end: int, new_lines: list[str]
) -> list[str]:
    new_content = []
    index = 0
    skip = end - start - 1

    while index != (start + 1):
        new_content.append(lines[index])
        index += 1

    new_content.extend(iter(new_lines))
    index += skip
    while index < len(lines):
        new_content.append(lines[index])
        index += 1

    return new_content

def find_and_replace_smali_line(
    lines: list[str], search: str, replace: str
) -> list[str]:
    for index, line in enumerate(lines):
        if line.find(search) >= 0:
            lines[index] = lines[index].replace(search, replace)
    return lines
