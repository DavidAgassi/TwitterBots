import json


def parse_line(i, v):
    splitted = v.strip().split(" ")
    line_dict = {
        "line_ind": i,
        "line_text": " ".join(splitted[1:])
    }
    return line_dict


with open("GilgameshBot/Gilgamesh.txt", 'r') as fin:
    raw = fin.readlines()

raw = list(filter(lambda s: s != '\n', raw))
parsed = list()
tablet_ind = 0
for l in raw:
    if l.startswith("לוּחַ "):
        tablet_heb_ind = l.strip().split(" ")[1]
        lines = list()
        line_ind = 0
        tablet_dict = {
            "tablet_ind": tablet_ind,
            "tablet_heb_ind": tablet_heb_ind,
            "lines": lines
        }
        parsed.append(tablet_dict)
        tablet_ind = tablet_ind + 1
    else:
        line_dict = {
            "line_text": l.strip(),
            "line_ind": line_ind
        }
        line_ind = line_ind + 1
        lines.append(line_dict)

with open("GilgameshBot/parsed_gilgamesh.json", 'w') as fout:
    json.dump(parsed, fout)
