#!/usr/bin/env python

from sys import argv
from getopt import getopt
from math import ceil

rank_format_string = "%f\t%f\t%f\t%d\t%d"
def get_header():
    return "Energy\tScore\tFrequency\tBetter_Count\tRank"

class Rank():
    def __init__(self,energy,score,freq):
        self.energy = energy
        self.score = score
        self.freq = freq
        self.sum = 0
        self.rank = 0

    def __str__(self):
        return rank_format_string % (self.energy, self.score, self.freq, self.sum, self.rank)
    
    def __lt__(self,rhs):
        if self.energy > rhs.energy:
            return True
        if self.energy == rhs.energy:
            return self.score < rhs.score
        return False

    def __eq__(self,rhs):
        return self.energy == rhs.energy and self.score == rhs.score

def str2rank(line):
    tokens = line.split("\t")
    if len(tokens) < 2:
        print("Invalid line. Need frequency and score-energy token.")
        print("Line: %s" % line)
        exit(1)
    freq = float(tokens[1])
    tokens = tokens[0].split(":")
    if len(tokens) < 2:
        print("Invalid line. Energy and score separated by ':'")
        print("Line: %s" % line)
        exit(1)
    
    return Rank(float(tokens[0]),float(tokens[1]),freq)

def find_file():
    from glob import glob
    files = glob("*.score_count.ordered")
    if not files:
        return None
    return files[0]


short_opts = "si"
long_opts = ["intermediate","search","no_header"]

(opts,args) = getopt(argv[1:],short_opts,long_opts)

should_search = False
have_header = True
show_intermediate = False
for (opt,optarg) in opts:
    while opt[0] == "-":
        opt = opt[1:]
    if opt in ["s","search"]:
        should_search = True
    elif opt in ["i","intermediate"]:
        show_intermediate = True
    elif opt == "no_header":
        have_header = True
    else:
        print("Unknown flag: %s" % opt)
        exit(1)

file = None    
if should_search:
    filename = find_file()
    if not filename:
        print("Could not find score_count file")
        exit(1)
    file = open(filename,"r")
else:
    if len(args) < 1:
        print("Usage: energy_score_ranker.py <FILE>")
        exit(1)
    file = open(args[0],"r")
in_filename = file.name

if have_header:
    file.readline() # skip header

ranks = []
for line in file:
    line = line.strip()
    val = str2rank(line)
    ranks.append(val)

if show_intermediate:
    print(get_header())
ranks = sorted(ranks)
num_ranks = len(ranks)
total_hits = 0
ordered_ranks = {}
for i in range(0,num_ranks):
    total_hits += ranks[i].freq
    ranks[i].sum = 0
    curr_rank = num_ranks-i
    ranks[i].rank = curr_rank
    for j in range(i+1,num_ranks):
        ranks[i].sum += ranks[j].freq
    if show_intermediate:
        print(ranks[i])
    if curr_rank in ordered_ranks:
        ordered_ranks[curr_rank].append(ranks[i])
    else:
        ordered_ranks[curr_rank] = [ranks[i]]

outfile = open(in_filename + ".ordered","w")
top_quartile = open("top_25-percent.dat","w")
for f in [outfile,top_quartile]:
    f.write(get_header())
    f.write("\n")
q = ceil(len(ranks)*0.25)
q_counter = 0
for key in sorted(ordered_ranks.iterkeys()):
    for rank in ordered_ranks[key]:
        outstring = "%s\n" % rank
        if q_counter < q:
            top_quartile.write(outstring)
        q_counter += rank.rank
        outfile.write(outstring)
    

file.close()

