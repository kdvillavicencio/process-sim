import itertools

''' EXAMPLE INPUT DICTS
paramBounds_sample = {
    "T": (100,200,5),
    "P": (1,5,4),
    "m": (200,300,2)
}

compositions_sample = {
    "s1": [[0.4,0.4,0.2],[0.2,0.2,0.3]]
}
'''

def generate_dataspace(paramBounds, compositions):
    paramPoints = {}
    dataspace = []

    # PARAMETER RANGE
    for param in paramBounds.keys():
        (min, max, step_count) = paramBounds[param]
        step_size = ((max-min)/step_count)
        paramPoints[param] = []
        for i in range(int(step_count)+1):
            point = min + (i*step_size)
            paramPoints[param].append(point)

    # COMPOSITIONS
    for stream in compositions.keys():
        paramPoints[stream] = compositions[stream]

    # GENERATING DATASPACE
    # itertools.combinations returns a generator and not a list. 
    # What this means is that you can iterate over it but not access it element by element with an index as you are attempting to.
    # https://stackoverflow.com/questions/28199603/typeerror-itertools-combinations-object-is-not-subscriptable
    for val in itertools.product(*paramPoints.values()):
        dataspace.append(val)

    paramKeys = paramPoints.keys()
    return (paramKeys, dataspace)

# NOTES
# feature size is only as many as the declared params
# cartesian product of the values will determine the number of sim runs

'''
# GET INDIVIDUAL RUN
paramKeys = paramPoints.keys()
for item in dataspace:
  data = dict(zip(paramKeys,item))
  # print(data)
'''