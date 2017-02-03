import LargeVis
import argparse
import fileinput #for reading large files
import json
import random
import numpy as np
import os
import shutil
import csv 
import math
from datetime import datetime
import argparse as argp

parser = argparse.ArgumentParser(description = 'This script performs embedding of a sparse similarity matrix into coordinates and opens the DiVE viewer with the result .')
parser.add_argument('-fea', default = 0, type = int, help = 'whether to visualize high-dimensional feature vectors or networks')
parser.add_argument('-input', default = '', help = 'input file')
parser.add_argument('-output', default = '', help = 'output coordinates file')
parser.add_argument('-outdim', default = -1, type = int, help = 'output dimensionality')
parser.add_argument('-threads', default = -1, type = int, help = 'number of training threads')
parser.add_argument('-samples', default = -1, type = int, help = 'number of training mini-batches')
parser.add_argument('-prop', default = -1, type = int, help = 'number of propagations')
parser.add_argument('-alpha', default = -1, type = float, help = 'learning rate')
parser.add_argument('-trees', default = -1, type = int, help = 'number of rp-trees')
parser.add_argument('-neg', default = -1, type = int, help = 'number of negative samples')
parser.add_argument('-neigh', default = -1, type = int, help = 'number of neighbors in the NN-graph')
parser.add_argument('-gamma', default = -1, type = float, help = 'weight assigned to negative edges')
parser.add_argument('-perp', default = -1, type = float, help = 'perplexity for the NN-grapn')



parser.add_argument(
   '-metadata',
   default = 'No',
   dest = 'metaDataFile',
   help = 'Input file containing the properties(text) accompanying the data. Format: [id] [metadata] . Metadata format: "first_line" "second_line" "third_line" ..."n_line"')

parser.add_argument(
   '-dir',
   default = os.getcwd(), 
   dest = 'baseDir',
   help = 'Base directory to store output files')

parser.add_argument(
   '-np', 
   default = 'No', 	
   dest = 'namesOfPropertiesFile',
   help = 'A json file containing list of properties names. Ex ["Name", "DBSCAN label", "K-means label"]')

parser.add_argument(
   '-json', 
   default = 'data.json', 	
   dest = 'jsonFileName',
   help = 'Name of the output json file, which is input to DiVE')

parser.add_argument(
   '-divedir',
   default = os.getcwd(), 	
   dest = 'diveDir',
   help = 'Directory where DiVE resides')

args = parser.parse_args()

if args.fea == 1:
    LargeVis.loadfile(args.input)
else:
    LargeVis.loadgraph(args.input)

Y = LargeVis.run(args.outdim, args.threads, args.samples, args.prop, args.alpha, args.trees, args.neg, args.neigh, args.gamma, args.perp)

LargeVis.save(args.output)

########################## LargeVis has finished, now we generate data for DiVE

def ReadMetaDataFile(metaDataFile):
        """File format: [id] [metadata] 
        metadata format: "first_line" "second_line" "third_line" ... "n_line" """
        metaDataDict = dict()
        for line in fileinput.input([metaDataFile]):
            if line != "\n":   
                for items in csv.reader([line], delimiter=' ', quotechar='"'): 
                    id = items[0]     
                    items.pop(0)                             
                    metaDataDict[id] = items
        return metaDataDict


def ReadCoordinates(file):     
    fixed = dict()
    maxabs = 0
    for line in fileinput.input([file]):
        if line != "\n":   
            items = line.split()
            if len(items) > 2:# to skip the first line 
                if (len(items) ==3): #if dimension == 2
                    maxabs = max(abs(float(items[1])), abs(float(items[2])), maxabs)
                    fixed[items[0]] = [ 0.1, float(items[1]), float(items[2])] # add artificial x-dimension. must be non-zero
                else:
                    maxabs = max(abs(float(items[1])), max(abs(float(items[2])), abs(float(items[3]))), maxabs)
                    fixed[items[0]] = [float(items[1]), float(items[2]), float(items[3])]
    for key in fixed.keys():
        lis = fixed[key]
        fixed[key] = [lis[0]/maxabs, lis[1]/maxabs, lis[2]/maxabs]
    return fixed

def CreateSmallDataJSONFile(allPoints, startingFolder,  jsonfilename):
    string = json.dumps(allPoints) 
    if jsonfilename == "None":
	jsonfilename = "data.json"	
    if startingFolder == "None":
	startingFolder = os.getcwd()
    print(startingFolder)
    print(jsonfilename)
    
    filepath = os.path.join(startingFolder, jsonfilename)	 
    	
    file = open(filepath, "w")
    file.write(string)
    file.close()  	 	
    file = open(os.path.join( args.diveDir, "DiVE", "data", "data.js"), "w")
    string = "const data_all = " + string  		
    file.write(string)
    file.close()		

	

def CreatePointsDictionary(fixedCoordinates,  metaDataDict,  namesOfPropertiesFile):
    pointsDict = dict()
    if namesOfPropertiesFile != "No":
        with open(namesOfPropertiesFile) as json_data:
            list = json.load(json_data)
        pointsDict["NamesOfProperties"] = list
    for key in fixedCoordinates.keys():
        point = dict()
        point["Coordinates"] = fixedCoordinates[key]
        if (metaDataDict != "no" ):
            if key in metaDataDict:
                point["Properties"] = metaDataDict[key]
            else:
                point["Properties"] = []
        else: 
            point["Properties"] = []
        pointsDict[key] = point
    return pointsDict


def CreateDirIfDoesNotExist(dirname):
    if not os.path.exists(dirname):          
        os.makedirs(dirname)

def RemoveDirTreeIfExists(dirname):        
    if os.path.exists(dirname):
        shutil.rmtree(dirname)

def ConvertCoordinatesToList(fixedCoordinate):
    for key in fixedCoordinate:
        fixedCoordinate[key] = list(fixedCoordinate[key])
                       
def Workflow(coordinatesFile, metaDataFile, namesOfPropertiesFile, baseDir = os.getcwd(), jsonfilename = "data.json"):      
    """Produces the input for DiVE. 
       coordinatesFile is the output of LargeVis
       metaDataFile contains info about the photos
       namesOfPropeties file contains a list of names of properties. Ex ["Name", "DBSCAN label", "K-means label"]
       baseDir - where to write output
       jsonfilename - the name of the output file
    """
    	
    dirname1 = baseDir;
    print(str(datetime.now()) + ": Reading input files...")
    if metaDataFile != "No":
        metaDataDict = ReadMetaDataFile(metaDataFile)
    else: 
        metaDataDict = "no"          
    fixedCoordinate = ReadCoordinates(coordinatesFile)
    ConvertCoordinatesToList(fixedCoordinate)   
    pointsDict = CreatePointsDictionary(fixedCoordinate, metaDataDict,  namesOfPropertiesFile)        
    print(str(datetime.now()) + ": Start writing output...")         
    CreateDirIfDoesNotExist(dirname1)
    CreateSmallDataJSONFile(pointsDict, dirname1, jsonfilename)
    print(str(datetime.now()) + ": Finished writing output.")


if __name__ == "__main__":
    Workflow(args.output, args.metaDataFile, args.namesOfPropertiesFile,  args.baseDir, args.jsonFileName)

# now opening the browser


import webbrowser
new = 2 # open in a new tab, if possible
url = args.diveDir + "/DiVE/index.html"
webbrowser.open(url,new=new)



