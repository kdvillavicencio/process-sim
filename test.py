import input_params as inputs
import polars as pl

components = {
    "s1": ["Water", "Ethanol","Acetone"],
    "s2": ["C1", "C2","C3"]
}

paramBounds = {
  "T": (300,350,2),
  "P": (101325,202650,2),
  "m": (300,400,2)
}

compositions = {
  "s1": [[0.4,0.4,0.2]],
  "s2": [[0.2,0.3,0.5]]
}

(paramKeys, dataspace) = inputs.generate_dataspace(paramBounds, compositions)

inputs = pl.from_dict({list(paramKeys)[i]:[*(data[i] for data in dataspace)] for i in range(len(list(paramKeys)))})

# out = inputs.select([
#     listCol.list.get(0).alias(f"{listCol.meta.output_name()[0]}_a") for listCol in [pl.col(pl.List(pl.Float64))]    
#     ])

# listCols = inputs.select([
#     pl.col(pl.List(pl.Float64))
# ])

## NESTED SYNTAX 
component_expr = []
for stream in components.keys():
    for i in range(len(components[stream])):
      component_expr.append(pl.col(stream).list.get(i).alias(f"{stream}_{components[stream][i]}"))

inputs = inputs.select(
   [pl.exclude(pl.List(pl.Float64)),*component_expr,]
)

print(inputs)

''' LESSONS
- args to df.select() should be pl.Expr instance
- dtype of columns can be passed to exclusion and selection
  - select by `pl.col()` (name or dtype)
  - exclude by `pl.exclude()` (name or dtype)
'''