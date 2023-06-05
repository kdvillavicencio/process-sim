import input_params as inputs
import polars as pl
import os

import pythoncom
pythoncom.CoInitialize()

import clr

from System.IO import Directory, Path, File
from System import String, Environment

dwsimpath = "C:\\Users\\MSI\\AppData\\Local\\DWSIM\\"

clr.AddReference(dwsimpath + "CapeOpen.dll")
clr.AddReference(dwsimpath + "DWSIM.Automation.dll")
clr.AddReference(dwsimpath + "DWSIM.Interfaces.dll")
clr.AddReference(dwsimpath + "DWSIM.GlobalSettings.dll")
clr.AddReference(dwsimpath + "DWSIM.SharedClasses.dll")
clr.AddReference(dwsimpath + "DWSIM.Thermodynamics.dll")
clr.AddReference(dwsimpath + "DWSIM.UnitOperations.dll")
clr.AddReference(dwsimpath + "DWSIM.Inspector.dll")
clr.AddReference(dwsimpath + "System.Buffers.dll")

from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType
from DWSIM.Thermodynamics import Streams, PropertyPackages
from DWSIM.UnitOperations import UnitOperations
from DWSIM.Automation import Automation3
from DWSIM.GlobalSettings import Settings
from System import Array

Directory.SetCurrentDirectory(dwsimpath)

# create automation manager

manager = Automation3()

myflowsheet = manager.CreateFlowsheet()

### DEFINE PARAMETERS
components = {
    "s1": ["Water", "Ethanol","Acetone"],
    # "s2": ["C1", "C2","C3"]
}

paramBounds = {
  "T": (300,350,2),
  "P": (101325,202650,2),
  "m": (300,400,2)
}

compositions = {
  "s1": [[0.4,0.4,0.2]]
}


myflowsheet.AddCompound("Water")
myflowsheet.AddCompound("Ethanol")
myflowsheet.AddCompound("Acetone")

# create and connect objects

feed  = myflowsheet.AddObject(ObjectType.MaterialStream, 50, 50, "Feed")
dist = myflowsheet.AddObject(ObjectType.MaterialStream, 150, 50, "Distillate")
bottoms = myflowsheet.AddObject(ObjectType.MaterialStream, 150, 50, "Bottoms")
column = myflowsheet.AddObject(ObjectType.DistillationColumn, 100, 50, "Column")

feed = feed.GetAsObject()
dist = dist.GetAsObject()
bottoms = bottoms.GetAsObject()
column = column.GetAsObject()

# change number of stages - default is 10

column.SetNumberOfStages(12)

# connect streams to column

column.ConnectFeed(feed, 6)
column.ConnectDistillate(dist)
column.ConnectBottoms(bottoms)

myflowsheet.NaturalLayout()

(paramKeys, dataspace) = inputs.generate_dataspace(paramBounds, compositions)
##  inputs = {list(paramKeys)[i]:[*(data[i] for data in dataspace)] for i in range(len(list(paramKeys)))}
# create a dict with keys from the `paramKeys` list
# - `paramKeys` is still a dict so `list(paramKeys)` is used
# - we want to use the index of the key to get the corresponding value from the dataspace
# - therefore, a for-loop from the range of the length is used
# create a list composed of the values of the param at all rows
# - for loop of the data space can be used
# - from the individual dataspace item (data), the param value is taken using the index
# - expand the resulting list using *args syntax
inputs_df = pl.from_dict({list(paramKeys)[i]:[*(data[i] for data in dataspace)] for i in range(len(list(paramKeys)))})

## NESTED SYNTAX 
component_expr = []
for stream in components.keys():
  for i in range(len(components[stream])):
    component_expr.append(pl.col(stream).list.get(i).alias(f"{stream}_{components[stream][i]}"))

inputs_df = inputs_df.select(
  [pl.exclude(pl.List(pl.Float64)),*component_expr,]
)

resultKeys = ["cduty", "rduty", "dtemp", "dflow", "btemp", "bflow" ]
outputs = {k:[] for k in resultKeys}

outputs.update({f"d_{k}":[] for k in components["s1"]})
outputs.update({f"b_{k}":[] for k in components["s1"]})

### CALCULATION LOOP
for paramValues in dataspace:
  # Consider rewriting using polars dataframe directly
  data = dict(zip(paramKeys,paramValues))

  feed.SetOverallComposition(Array[float](data["s1"]))
  feed.SetTemperature(data["T"]) # K
  feed.SetPressure(data["P"]) # Pa
  feed.SetMolarFlow(data["m"]) # mol/s

  # allowed specs:

  # Heat_Duty = 0
  # Product_Molar_Flow_Rate = 1
  # Component_Molar_Flow_Rate = 2
  # Product_Mass_Flow_Rate = 3
  # Component_Mass_Flow_Rate = 4
  # Component_Fraction = 5
  # Component_Recovery = 6
  # Stream_Ratio = 7
  # Temperature = 8

  column.SetCondenserSpec("Reflux Ratio", 3.0, "")
  column.SetReboilerSpec("Product_Molar_Flow_Rate", 200.0, "mol/s")

  # property package

  nrtl = myflowsheet.CreateAndAddPropertyPackage("NRTL")

  # request a calculation

  errors = manager.CalculateFlowsheet4(myflowsheet)

  # get condenser and reboiler duties

  outputs["cduty"].append(column.CondenserDuty)   # kW
  outputs["rduty"].append(column.ReboilerDuty)    # kW

  outputs["dtemp"].append(dist.GetTemperature())  # K
  outputs["dflow"].append(dist.GetMolarFlow())    # mol/s
  outputs["btemp"].append(bottoms.GetTemperature())   # K
  outputs["bflow"].append(bottoms.GetMolarFlow())     # mol/s

  # product compositions

  dcomp = dist.GetOverallComposition()
  for i in range(len(components['s1'])):
    outputs[f"d_{components['s1'][i]}"].append(dcomp[i])

  bcomp = bottoms.GetOverallComposition()
  for i in range(len(components['s1'])):
    outputs[f"b_{components['s1'][i]}"].append(dcomp[i])

# save files


outputs_df = pl.from_dict(outputs)
print(inputs_df.head(5))
print(outputs_df.head(5))
# df.write_csv("new.csv", separator=",")
rootdir = os.path.dirname(__file__)
inputs_df.write_csv(os.path.join(rootdir, "outputs/inputs.csv"), separator=",")
outputs_df.write_csv(os.path.join(rootdir, "outputs/outputs.csv"), separator=",")
