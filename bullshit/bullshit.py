#!/usr/bin/env python

import random as r

def bullshit():
    verbs = [line.strip() for line in open("./verbs.txt")]
    adjectives = [line.strip() for line in open("./adjectives.txt")]
    nouns = [line.strip() for line in open("./nouns.txt")]

    return "{} {} {}".format(r.choice(verbs), r.choice(adjectives), r.choice(nouns))

if __name__ == "__main__":
    print(bullshit())
