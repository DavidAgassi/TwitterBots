import json


def parse_verse(i, v):
    splitted = v.strip().split(" ")
    verse_dict = {
        "verse_ind": i,
        "verse_heb_ind": splitted[0],
        "verse_text": " ".join(splitted[1:])
    }
    return verse_dict


with open("TehilimBot/tehilim.txt", 'r') as fin:
    raw = fin.readlines()

raw = list(filter(lambda s: s != '\n', raw))
parsed = list()
for i in range(150):
    chapter_heb_ind = raw[2 * i].strip().split(" ")[1]
    verses = list(filter(lambda s: len(s) > 0, raw[2*i + 1].strip().split(":")))
    chap_dict = {
        "chapter_ind": i,
        "chapter_heb_ind": chapter_heb_ind,
        "verses": [parse_verse(i, v) for i, v in enumerate(verses)]
    }
    parsed.append(chap_dict)

with open("TehilimBot/parsed_tehilim.json", 'w') as fout:
    json.dump(parsed, fout)
