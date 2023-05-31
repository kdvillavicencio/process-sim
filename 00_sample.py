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

feed.SetOverallComposition(Array[float]([0.4, 0.4, 0.2]))
feed.SetTemperature(350.0) # K
feed.SetPressure(101325.0) # Pa
feed.SetMolarFlow(300.0) # mol/s

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

cduty = column.CondenserDuty
rduty = column.ReboilerDuty

print("Condenser Duty: " + str(cduty) + " kW")
print("Reboiler Duty: " + str(rduty) + " kW")

dtemp = dist.GetTemperature()
dflow = dist.GetMolarFlow()
btemp = bottoms.GetTemperature()
bflow = bottoms.GetMolarFlow()

print()
print("Distillate Temperature: " + str(dtemp) + " K")
print("Bottoms Temperature: " + str(btemp) + " K")

print()
print("Distillate Molar Flow: " + str(dflow) + " mol/s")
print("Bottoms Molar Flow: " + str(bflow) + " mol/s")

# product compositions

print()

distcomp = dist.GetOverallComposition()
print("Distillate Molar Composition:")
for i in range(0, 3):
	print(cnames[i] + ": " + str(distcomp[i]))
	i+=1

print()

bcomp = bottoms.GetOverallComposition()
print("Bottoms Molar Composition:")
for i in range(0, 3):
	print(cnames[i] + ": " + str(bcomp[i]))
	i+=1

# save file

fileNameToSave = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop), "python_column_sample.dwxmz")

manager.SaveFlowsheet(myflowsheet, fileNameToSave, True)

# save the pfd to an image and display it

clr.AddReference(dwsimpath + "SkiaSharp.dll")
clr.AddReference("System.Drawing")

from SkiaSharp import SKBitmap, SKImage, SKCanvas, SKEncodedImageFormat
from System.IO import MemoryStream
from System.Drawing import Image
from System.Drawing.Imaging import ImageFormat

PFDSurface = myflowsheet.GetSurface()

imgwidth = 1024
imgheight = 768

bmp = SKBitmap(imgwidth, imgheight)
canvas = SKCanvas(bmp)
PFDSurface.Center(imgwidth, imgheight)
PFDSurface.ZoomAll(imgwidth, imgheight)
PFDSurface.UpdateCanvas(canvas)
d = SKImage.FromBitmap(bmp).Encode(SKEncodedImageFormat.Png, 100)
str = MemoryStream()
d.SaveTo(str)
image = Image.FromStream(str)
imgPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop), "pfd.png")
image.Save(imgPath, ImageFormat.Png)
str.Dispose()
canvas.Dispose()
bmp.Dispose()

from PIL import Image

im = Image.open(imgPath)
im.show()