from txbeatlounge.music.constants import twelve_tone_equal_440

shrutis = {
0: (1/1.,),
1: (256/243., 16/15.),
2: (10/9., 9/8.),
3: (32/27., 6/5.),
4: (5/4., 81/64.),
5: (4/3.,),
# 27/20.,
6: (45/32., 729/512.),
7: (3/2.,),
8: (128/81., 8/5.),
9: (5/3., 27/16.),
10: (16/9., 9/5.),
11: (15/8., 243/128.),
12: (2,),
14: (18/8.,),
17: (12/5.,),
21: (10/3.,),
}

offsets = {}
for k, v in shrutis.iteritems():
    offsets[k] = []
    for val in v:
        offsets[k].append(440*val/twelve_tone_equal_440[57+k])


def getCentsMultiplier(cents):
    return 2**(cents/1200.)

