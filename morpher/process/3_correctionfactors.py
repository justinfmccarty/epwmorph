import pandas as pd
import numpy as np
import datetime as dt
from pathlib import Path

"""
This is the third script in morphing script. In it the percentiles are accessed
per variable and the various correction factors for each future period are
calculated.

Note: It was easier to calcuate the shift and stretch factor for each variable
even though each variable does not necessarily need both factors in the morphing
proecedure. This could be fixed later on, but is not a hinderance currently.
"""

# open config and format
configpath = r"C:\Users\justi\Dropbox\UBC\8 Spring 2020\DS7_ Passive Principles for a Chang(ing)ed Climate\6_morpher\config.txt"
config = pd.DataFrame(pd.read_csv(configpath,header=None,index_col=0,delimiter="`"))

# grad details from the config file
root =  config.at['root',1]
model =  config.at['model directory',1]
project = config.at['project name',1]
scenario1 = config.at['scenario1',1]
scenario2 = config.at['scenario2',1]
scenario3 = config.at['scenario3',1]
lati =  float(config.at['latitude',1])
loni = float(config.at['longitude',1])
alt = int(float(config.at['elevation(m)',1]))
baselinestart = config.at['baselinestart',1]
baselineend = config.at['baselineend',1]
future1start = config.at['future1start',1]
future1end = config.at['future1end',1]
future2start = config.at['future2start',1]
future2end = config.at['future2end',1]
future3start = config.at['future3start',1]
future3end = config.at['future3end',1]
# specify the variables to grab and add to variable list
var1 = 'tas' # will transform to Celsius
var2 = 'tasmax'
var3 = 'tasmin'
var4 = 'clt' #will tranform to tenth rounding down
var5 = 'hurs' #will transform into hurs
var6 = 'pr'
var7 = 'psl' #will transform into station pressure
var8 = 'windsfc'
var9 = 'winddir' #will transform into windSfc and windDir
var10 = 'rsds'
# specify the list of variables (need at least two)
varlist = (var1,var2,var3,var4,var5,var6,var7,var8,var9,var10)

scen1 = 'ssp126'
scen2 = 'ssp245'
scen3 = 'ssp585'
scenlist = (scen1,scen2,scen3)
for scen in scenlist:
    bracketlist=[]
    for var in varlist:
        percentile = (root + "data" + '\\{PROJ}\\{SCEN}\\percentile\\{VAR}_1950-2100_{SCEN}.csv').format(PROJ=project,SCEN=scen,VAR=var)
        df = pd.DataFrame(pd.read_csv(percentile,header=0,parse_dates=[0],index_col=[0]))
        hstart = baselinestart + "-01-01"
        hend = baselineend + "-12-31"
        fstart1 = future1start + "-01-01"
        fend1 = future1end + "-12-31"
        fstart2 = future2start + "-01-01"
        fend2 = future2end + "-12-31"
        fstart3 = future3start + "-01-01"
        fend3 = future3end + "-12-31"
        historical = df[hstart:hend]
        future1 = df[fstart1:fend1]
        future2 = df[fstart2:fend2]
        future3 = df[fstart3:fend3]
        # mask dataframe to create the subframes for each period
        historical = df[hstart:hend]
        future1 = df[fstart1:fend1]
        future2 = df[fstart2:fend2]
        future3 = df[fstart3:fend3]
        historicalmean = historical.groupby([historical.index.month]).mean()
        future1mean = future1.groupby([future1.index.month]).mean()
        future2mean = future2.groupby([future2.index.month]).mean()
        future3mean = future3.groupby([future3.index.month]).mean()

        shiftfactor1 = future1mean - historicalmean
        stretchfactor1 = future1mean / historicalmean
        shiftfactor2 = future2mean - historicalmean
        stretchfactor2 = future2mean / historicalmean
        shiftfactor3 = future3mean - historicalmean
        stretchfactor3 = future3mean / historicalmean

        shiftout1 = (root + "data" + '\\{PROJ}\\{SCEN}\\correction\\shift_{VAR}_{START}-{END}_{SCEN}.csv').format(PROJ=project,SCEN=scen,VAR=var,START=future1start,END=future1end)
        stretchout1 = (root + "data" + '\\{PROJ}\\{SCEN}\\correction\\stretch_{VAR}_{START}-{END}_{SCEN}.csv').format(PROJ=project,SCEN=scen,VAR=var,START=future1start,END=future1end)
        shiftfactor1.to_csv(shiftout1,header=True)
        stretchfactor1.to_csv(stretchout1,header=True)
        shiftout2 = (root + "data" + '\\{PROJ}\\{SCEN}\\correction\\shift_{VAR}_{START}-{END}_{SCEN}.csv').format(PROJ=project,SCEN=scen,VAR=var,START=future2start,END=future2end)
        stretchout2 = (root + "data" + '\\{PROJ}\\{SCEN}\\correction\\stretch_{VAR}_{START}-{END}_{SCEN}.csv').format(PROJ=project,SCEN=scen,VAR=var,START=future2start,END=future2end)
        shiftfactor2.to_csv(shiftout2,header=True)
        stretchfactor2.to_csv(stretchout2,header=True)
        shiftout3 = (root + "data" + '\\{PROJ}\\{SCEN}\\correction\\shift_{VAR}_{START}-{END}_{SCEN}.csv').format(PROJ=project,SCEN=scen,VAR=var,START=future3start,END=future3end)
        stretchout3 = (root + "data" + '\\{PROJ}\\{SCEN}\\correction\\stretch_{VAR}_{START}-{END}_{SCEN}.csv').format(PROJ=project,SCEN=scen,VAR=var,START=future3start,END=future3end)
        shiftfactor3.to_csv(shiftout3,header=True)
        stretchfactor3.to_csv(stretchout3,header=True)

        hseries = pd.DataFrame(historicalmean['0.5'])
        hseries = hseries.rename(columns={"0.5":var})
        bracketlist.append(hseries)
    bracket = pd.DataFrame(pd.concat(bracketlist,axis=1))
    historical = (root + "data" + '\\{PROJ}\\{SCEN}\\historicalmean_{hSTART}-{hEND}_{SCEN}.csv').format(PROJ=project,SCEN=scen,VAR=var,hSTART=baselinestart,hEND=baselineend)
    bracket.to_csv(historical,header=True)
print('Completed Task')
