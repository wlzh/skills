"""从 movies/202607.md 删除旧的那批链接（e9f695c 提交引入的）"""
import re

old_links = [
    "f088bcea80ff", "6c7861ce4314", "3770a0d00041", "dbb1f5d7fd5d",
    "276be22d1efa", "34e2d80444c6", "04fd68d54517", "4af1a52e57d3",
    "5baf78b460f9", "e821f4481d92", "30bce2762ce5", "41300ad81aae",
    "b99da0e12862", "22689230f89f", "d104737da23e", "f1f26c2763bb",
    "64394872647a", "a50bb7c857f2", "851c71ec7ae4", "d4e1e8db62e8",
    "f3ce4cd126eb", "ace81a59e481", "9a1be10a72bf", "a748d34e8c92",
    "88bdd9dbcd7c", "cbe89494a34f", "b73035aa3a07", "2d650ed1aed1",
    "cd90341771e6", "0c15e08e71f1", "fbac8882388f", "f54851a0f031",
    "4be67bcc2656", "1bc31cb42992",
    # 新片合集的6条
    "2f37ea391361", "2e67f716fb8b", "27dc23ecfe6f",
    "f8accb967ab2", "b7784b364143", "edc3b953f65f",
]

path = "/Users/m/document/QNSZ/project/mswnlz-github/movies/202607.md"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
removed = 0
for line in lines:
    if any(code in line for code in old_links):
        removed += 1
        continue
    new_lines.append(line)

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"删除 {removed} 行旧链接，剩余 {len(new_lines)} 行")
