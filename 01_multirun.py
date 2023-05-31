import input_params as inputs
import polars as pl

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

# add compounds

cnames = ["Water", "Ethanol","Acetone"]

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

### DEFINE PARAMETERS

paramBounds = {
  "T": (300,350,2),
  "P": (101325,202650,2),
  "m": (300,400,2)
}

compositions = {
  "s1": [[0.4,0.4,0.2]]
}

(paramKeys, dataspace) = inputs.generate_dataspace(paramBounds, compositions)

resultKeys = ["cduty", "rduty", "dtemp", "dflow", "btemp", "bflow" ]
results = {k:[] for k in resultKeys}

results.update({f"d_{k}":[] for k in cnames})
results.update({f"b_{k}":[] for k in cnames})

### CALCULATION LOOP
for paramValues in dataspace:
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

  results["cduty"].append(column.CondenserDuty)   # kW
  results["rduty"].append(column.ReboilerDuty)    # kW

  results["dtemp"].append(dist.GetTemperature())  # K
  results["dflow"].append(dist.GetMolarFlow())    # mol/s
  results["btemp"].append(bottoms.GetTemperature())   # K
  results["bflow"].append(bottoms.GetMolarFlow())     # mol/s

  # product compositions

  dcomp = dist.GetOverallComposition()
  for i in range(len(cnames)):
    results[f"d_{cnames[i]}"].append(dcomp[i])

  bcomp = bottoms.GetOverallComposition()
  for i in range(len(cnames)):
    results[f"b_{cnames[i]}"].append(dcomp[i])

# save file
print("SAVING")
df = pl.from_dict(results)
print(df)
df.write_csv("new.csv", separator=",")
