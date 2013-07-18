import os, sys
from netCDF4 import Dataset
import numpy as np
import interp2D
from datetime import datetime, timedelta
from netCDF4 import num2date, date2num
import interpolation as interp
import IOwrite

import date
import grd
import clim2bry
import barotropic
import IOinitial
import plotData
import IOsubset

__author__   = 'Trond Kristiansen'
__email__    = 'trond.kristiansen@imr.no'
__created__  = datetime(2008, 8, 15)
__modified__ = datetime(2008, 8, 19)
__modified__ = datetime(2010, 1, 7)
__version__  = "1.5"
__status__   = "Development, modified on 15.08.2008,01.10.2009,07.01.2010"

def VerticalInterpolation(var,array1,array2,grdROMS,grdMODEL):

    outINDEX_ST   = (grdROMS.Nlevels,grdROMS.eta_rho,grdROMS.xi_rho)
    outINDEX_U    = (grdROMS.Nlevels,grdROMS.eta_u,grdROMS.xi_u)
    outINDEX_UBAR = (grdROMS.eta_u,grdROMS.xi_u)
    outINDEX_V    = (grdROMS.Nlevels,grdROMS.eta_v,grdROMS.xi_v)
    outINDEX_VBAR = (grdROMS.eta_v,grdROMS.xi_v)


    if var=='salinity' or var=='temperature':
        print 'Start vertical interpolation for %s (dimensions=%s x %s)'%(var,grdROMS.xi_rho,grdROMS.eta_rho)
        outdata=np.zeros((outINDEX_ST),dtype=np.float64, order='Fortran')

        outdata = interp.interpolation.dovertinter(np.asarray(outdata,order='Fortran'),
                                                       np.asarray(array1,order='Fortran'),
                                                       np.asarray(grdROMS.depth,order='Fortran'),
                                                       np.asarray(grdROMS.z_r,order='Fortran'),
                                                       np.asarray(grdMODEL.z_r,order='Fortran'),
                                                       int(grdROMS.Nlevels),
                                                       int(grdMODEL.Nlevels),
                                                       int(grdROMS.xi_rho),
                                                       int(grdROMS.eta_rho),
                                                       int(grdROMS.xi_rho),
                                                       int(grdROMS.eta_rho))


        #for k in range(grdROMS.Nlevels):
        plotData.contourMap(grdROMS,grdMODEL,np.squeeze(outdata[34,:,:]),34,var)

        return outdata


    if var=='vvel':
        print 'Start vertical interpolation for uvel (dimensions=%s x %s)'%(grdROMS.xi_u,grdROMS.eta_u)
        outdataU=np.zeros((outINDEX_U),dtype=np.float64)
        outdataUBAR=np.zeros((outINDEX_UBAR),dtype=np.float64)

        outdataU = interp.interpolation.dovertinter(np.asarray(outdataU,order='Fortran'),
                                                       np.asarray(array1,order='Fortran'),
                                                       np.asarray(grdROMS.depth,order='Fortran'),
                                                       np.asarray(grdROMS.z_r,order='Fortran'),
                                                       np.asarray(grdMODEL.z_r,order='Fortran'),
                                                       int(grdROMS.Nlevels),
                                                       int(grdMODEL.Nlevels),
                                                       int(grdROMS.xi_u),
                                                       int(grdROMS.eta_u),
                                                       int(grdROMS.xi_rho),
                                                       int(grdROMS.eta_rho))

        print 'Start vertical interpolation for vvel (dimensions=%s x %s)'%(grdROMS.xi_v,grdROMS.eta_v)
        outdataV=np.zeros((outINDEX_V),dtype=np.float64)
        outdataVBAR=np.zeros((outINDEX_VBAR),dtype=np.float64)

        outdataV = interp.interpolation.dovertinter(np.asarray(outdataV,order='Fortran'),
                                                       np.asarray(array2,order='Fortran'),
                                                       np.asarray(grdROMS.depth,order='Fortran'),
                                                       np.asarray(grdROMS.z_r,order='Fortran'),
                                                       np.asarray(grdMODEL.z_r,order='Fortran'),
                                                       int(grdROMS.Nlevels),
                                                       int(grdMODEL.Nlevels),
                                                       int(grdROMS.xi_v),
                                                       int(grdROMS.eta_v),
                                                       int(grdROMS.xi_rho),
                                                       int(grdROMS.eta_rho))

        z_wu=np.zeros((grdROMS.Nlevels+1,grdROMS.eta_u,grdROMS.xi_u), dtype=np.float64)
        z_wv=np.zeros((grdROMS.Nlevels+1,grdROMS.eta_v,grdROMS.xi_v), dtype=np.float64)



        outdataUBAR  = barotropic.velocity.ubar(np.asarray(outdataU,order='Fortran'),
                                                np.asarray(outdataUBAR,order='Fortran'),
                                                np.asarray(grdROMS.z_w,order='Fortran'),
                                                np.asarray(z_wu,order='Fortran'),
                                                grdROMS.Nlevels,
                                                grdROMS.xi_u,
                                                grdROMS.eta_u,
                                                grdROMS.xi_rho,
                                                grdROMS.eta_rho)

        plotData.contourMap(grdROMS,grdMODEL,outdataUBAR,"1","ubar")


        outdataVBAR  = barotropic.velocity.vbar(np.asarray(outdataV,order='Fortran'),
                                                np.asarray(outdataVBAR,order='Fortran'),
                                                np.asarray(grdROMS.z_w,order='Fortran'),
                                                np.asarray(z_wv,order='Fortran'),
                                                grdROMS.Nlevels,
                                                grdROMS.xi_v,
                                                grdROMS.eta_v,
                                                grdROMS.xi_rho,
                                                grdROMS.eta_rho)

        plotData.contourMap(grdROMS,grdMODEL,outdataVBAR,"1","vbar")

        return outdataU,outdataV,outdataUBAR,outdataVBAR


def HorizontalInterpolation(var,grdROMS,grdMODEL,data,show_progress):
    print 'Start %s horizontal interpolation for %s'%(grdMODEL.grdType,var)

    if grdMODEL.grdType=='regular':
        if var=='temperature':
            array1 = interp2D.doHorInterpolationRegularGrid(var,grdROMS,grdMODEL,data,show_progress)
        if var=='salinity':
            array1 = interp2D.doHorInterpolationRegularGrid(var,grdROMS,grdMODEL,data,show_progress)
        if var=='ssh':
            array1 = interp2D.doHorInterpolationSSHRegularGrid(var,grdROMS,grdMODEL,data)
        if var=='uvel':
            array1 = interp2D.doHorInterpolationRegularGrid(var,grdROMS,grdMODEL,data,show_progress)
        if var=='vvel':
            array1 = interp2D.doHorInterpolationRegularGrid(var,grdROMS,grdMODEL,data,show_progress)

    if grdMODEL.grdType=='irregular':
        if var=='temperature':
            interp2D.doHorInterpolationIrregularGrid(var,grdROMS,grdMODEL,data)
        if var=='salinity':
            interp2D.doHorInterpolationIrregularGrid(var,grdROMS,grdMODEL,data)
        if var=='ssh':
            interp2D.doHorInterpolationSSHIrregularGrid(var,grdROMS,grdMODEL,data)
        if var=='uvel':
            interp2D.doHorInterpolationIrregularGrid('uvel',grdROMS,grdMODEL,data)
        if var=='vvel':
            interp2D.doHorInterpolationIrregularGrid('vvel',grdROMS,grdMODEL,data)

    return array1

def rotate(grdROMS,grdMODEL,data,u,v):

        """
        First rotate the values of U, V at rho points with the angle, and then interpolate
        the rho point values to U and V points and save the result
        """

        urot=np.zeros((int(grdMODEL.Nlevels),int(grdROMS.eta_rho),int(grdROMS.xi_rho)), np.float64)
        vrot=np.zeros((int(grdMODEL.Nlevels),int(grdROMS.eta_rho),int(grdROMS.xi_rho)), np.float64)

        urot, vrot = interp.interpolation.rotate(np.asarray(urot,order='Fortran'),
                                                 np.asarray(vrot,order='Fortran'),
                                                 np.asarray(u,order='Fortran'),
                                                 np.asarray(v,order='Fortran'),
                                                 np.asarray(grdROMS.angle,order='Fortran'),
                                                 int(grdROMS.xi_rho),
                                                 int(grdROMS.eta_rho),
                                                 int(grdMODEL.Nlevels))
        return urot, vrot

def interpolate2UV(grdROMS,grdMODEL,urot, vrot):

        Zu=np.zeros((int(grdMODEL.Nlevels),int(grdROMS.eta_u),int(grdROMS.xi_u)), np.float64)
        Zv=np.zeros((int(grdMODEL.Nlevels),int(grdROMS.eta_v),int(grdROMS.xi_v)), np.float64)

        """
        Interpolate from RHO points to U and V points for velocities
        """


        Zu = interp.interpolation.rho2u(np.asarray(Zu,order='Fortran'),
                                        np.asarray(urot,order='Fortran'),
                                        int(grdROMS.xi_rho),
                                        int(grdROMS.eta_rho),
                                        int(grdMODEL.Nlevels))


        #plotData.contourMap(grdROMS,grdMODEL,Zu[0,:,:],"1",'urot')

        Zv = interp.interpolation.rho2v(np.asarray(Zv,order='Fortran'),
                                        np.asarray(vrot,order='Fortran'),
                                        int(grdROMS.xi_rho),
                                        int(grdROMS.eta_rho),
                                        int(grdMODEL.Nlevels))


        #plotData.contourMap(grdROMS,grdMODEL,Zv[0,:,:],"1",'vrot')

        return Zu, Zv

def getTime(cdf,grdROMS,grdMODEL,year,ID,type):

    """
    Create a date object to keep track of Julian dates etc.
    Also create a reference date starting at 1948/01/01.
    Go here to check results:http://lena.gsfc.nasa.gov/lenaDEV/html/doy_conv.html
    """
    ref_date = date.Date()
    ref_date.day=1
    ref_date.month=1
    ref_date.year=1948
    jdref=ref_date.ToJDNumber()

    if type=='HYCOM':
        dateHYCOM=str(cdf.variables["Date"][0])

        hycom_date = date.Date()
        hycom_date.day=int(dateHYCOM[6:8])
        hycom_date.month=int(dateHYCOM[4:6])
        hycom_date.year=int(dateHYCOM[0:4])
        jdhycom=hycom_date.ToJDNumber()

        grdROMS.time=(jdhycom-jdref)
        grdROMS.reftime=jdref

        print '\nCurrent time of HYCOM file : %s/%s/%s'%(hycom_date.year,hycom_date.month,hycom_date.day)

    if type=='SODA':
        """
        Find the day and month that the SODA file respresents based on the year and ID number.
        Each SODA file represents a 5 day average, therefore we let the date we find be the first day
        of those 5 days. Thats the reason we subtract 4 below for day of month.
        """
        days=0.0; month=1;loop=True

        while loop is True:

            d=date.NumberDaysMonth(month,year)
            if days+d<int(ID)*5:
                days=days+d
                month+=1
            else:
                day=int(int(ID)*5-days)
                loop=False

        soda_date = date.Date()
        soda_date.day=day
        soda_date.month=month
        soda_date.year=year
        jdsoda=soda_date.ToJDNumber()

        grdROMS.time=(jdsoda-jdref)
        grdROMS.reftime=jdref

        print '\nCurrent time of SODA file : %s/%s/%s'%(soda_date.year,soda_date.month,soda_date.day)

    if type=='SODAMONTHLY':
        """
        Find the day and month that the SODAMONTHLY file respresents based on the year and ID number.
        Each SODA file represents a 1 month average.
        """
        month=ID
        day=15

        soda_date = date.Date()
        soda_date.day=day
        soda_date.month=month
        soda_date.year=year
        jdsoda=soda_date.ToJDNumber()

        grdROMS.time=(jdsoda-jdref)
        grdROMS.reftime=jdref

        print '\nCurrent time of SODAMONTHLY file : %s/%s/%s'%(soda_date.year,soda_date.month,soda_date.day)
    
    if type=='GLORYS2V1':
        """
        Find the day and month that the SODAMONTHLY file respresents based on the year and ID number.
        Each SODA file represents a 1 month average.
        """
        month=ID
        day=15

        glorys_date = date.Date()
        glorys_date.day=day
        glorys_date.month=month
        glorys_date.year=year
        jdglorys=glorys_date.ToJDNumber()

        grdROMS.time=(jdglorys-jdref)
        grdROMS.reftime=jdref

        print '\nCurrent time of GLORYS2V1 file : %s/%s/%s'%(glorys_date.year,glorys_date.month,glorys_date.day)

def getGLORYS2V1filename(year,ID,myvar,dataPath):
    # Month indicates month
    # myvar:S,T,U,V
    if ID <  10: filename=dataPath+'global-reanalysis-phys-001-009-ran-fr-glorys2-grid'+str(myvar.lower())+'/REGRID/GLORYS2V1_ORCA025_'+str(year)+'0'+str(ID)+'15_R20110216_grid'+str(myvar.upper())+'_regrid.nc'
    if ID >= 10: filename=dataPath+'global-reanalysis-phys-001-009-ran-fr-glorys2-grid'+str(myvar.lower())+'/REGRID/GLORYS2V1_ORCA025_'+str(year)+str(ID)+'15_R20110216_grid'+str(myvar.upper())+'_regrid.nc'
    print filename
    return filename      
          
def convertMODEL2ROMS(years,IDS,climName,initName,dataPath,romsgridpath,vars,show_progress,type,subset):

    if type=='SODA':
        fileNameIn=dataPath+'SODA_2.0.2_'+str(years[0])+'_'+str(IDS[0])+'.cdf'
    if type=='SODAMONTHLY':
        fileNameIn=dataPath+'SODA_2.0.2_'+str(years[0])+'0'+str(IDS[0])+'.cdf'
    
    if type=='GLORYS2V1':
        """First opening of input file is just for initialization of grid"""
        fileNameIn=dataPath+'global-reanalysis-phys-001-009-ran-fr-glorys2-grids/REGRID/GLORYS2V1_ORCA025_'+str(years[0])+'0115_R20110216_gridS_regrid.nc'
        print fileNameIn
    if type=='HYCOM':
       fileNameIn=dataPath+'archv.2003_307_00_3zt.nc'

    """
    First time in loop, get the essential old grid information
    MODEL data already at Z-levels. No need to interpolate to fixed depths,
    but we use the one we have
    """
    grdMODEL = grd.grdClass(fileNameIn,type)
    grdROMS = grd.grdClass(romsgridpath,"ROMS")
    grdROMS.vars = vars

    """Now we want to subset the data to avoid storing more information than we need.
    We do this by finding the indices of maximum and minimum latitude and longitude in the matrixes"""
    if type=='SODA' or type=='SODAMONTHLY' or type=="GLORYS2V1":
        IOsubset.findSubsetIndices(grdMODEL,min_lat=subset[0], max_lat=subset[1], min_lon=subset[2], max_lon=subset[3])

    print 'Initializing done'
    print '\n--------------------------'

    time=0
    firstRun = True
    for year in years:

        for ID in IDS:

            if type=='SODA':
                file="SODA_2.0.2_"+str(year)+"_"+str(ID)+".cdf"
                filename=dataPath+file
                varNames=['TEMP','SALT','SSH','U','V']

            if type=='SODAMONTHLY':
                if ID <  10: filename=dataPath+'SODA_2.0.2_'+str(year)+'0'+str(ID)+'.cdf'
                if ID >= 10: filename=dataPath+'SODA_2.0.2_'+str(year)+str(ID)+'.cdf'
                varNames=['temp','salt','ssh','u','v']

            if type=='GLORYS2V1':
                filename=getGLORYS2V1filename(year,ID,"S",dataPath)
                varNames=['votemper','vosaline','sossheig','vozocrtx','vomecrty']
             

            if type=='HYCOM':
                filename=dataPath+'archv.2003_307_00_3zt.nc'
                varNames=['temperature','salinity','SSH','U','V'] 

            """Now open the input file"""
            cdf = Dataset(filename)
                
            getTime(cdf,grdROMS,grdMODEL,year,ID,type)

            """Each MODEL file consist only of one time step. Get the subset data selected, and
            store that time step in a new array:"""

            if firstRun is True:
                print "NOTICE!!: Make sure that these two arrays are in sequential order:"
                print "vars:     %s"%(vars)
                print "varnames: %s\n"%(varNames)
                firstRun = False
                if type=='SODA' or type=='SODAMONTHLY' or type=="GLORYS2V1":
                    """The first iteration we want to organize the subset indices we want to extract
                    from the input data to get the interpolation correct and to function fast"""
                    IOsubset.organizeSplit(grdMODEL,grdROMS,type,varNames,cdf)
                indexROMS_S_ST = (grdROMS.Nlevels,grdROMS.eta_rho,grdROMS.xi_rho)
                indexROMS_SSH  = (grdROMS.eta_rho,grdROMS.xi_rho)

                indexROMS_S_U = (grdROMS.Nlevels,grdROMS.eta_u,grdROMS.xi_u)
                indexROMS_S_V = (grdROMS.Nlevels,grdROMS.eta_v,grdROMS.xi_v)
                indexROMS_UBAR = (grdROMS.eta_u,grdROMS.xi_u)
                indexROMS_VBAR = (grdROMS.eta_v,grdROMS.xi_v)

            """
            All variables for all time are now stored in arrays. Now, start the interpolation to the
            new grid for all variables and then finally write results to file.
            """

            for var in vars:

                """Do the 3D variables first"""
                if var in ['temperature','salinity','uvel','vvel']:

                    if var=='temperature': varN=0; STdata=np.zeros((indexROMS_S_ST),dtype=np.float64)
                    if var=='salinity':    varN=1; STdata=np.zeros((indexROMS_S_ST),dtype=np.float64)
                    if var=='uvel':        varN=3; Udata = np.zeros((indexROMS_S_U),dtype=np.float64)
                    if var=='vvel':        varN=4; Vdata = np.zeros((indexROMS_S_V),dtype=np.float64)

    
                    """The variable splitExtract is defined in IOsubset.py and depends on the orientation
                    and type of grid (-180-180 or 0-360). Assumes regular grid."""
                    if grdMODEL.splitExtract is True:
                        if type=="SODA":
                            data1 = cdf.variables[varNames[varN]][0,:,
                                                     int(grdMODEL.indices[0,2]):int(grdMODEL.indices[0,3]),
                                                     int(grdMODEL.indices[0,0]):int(grdMODEL.indices[0,1])]
                            data2 = cdf.variables[varNames[varN]][0,:,
                                                     int(grdMODEL.indices[1,2]):int(grdMODEL.indices[1,3]),
                                                     int(grdMODEL.indices[1,0]):int(grdMODEL.indices[1,1])]
                        if type=="SODAMONTHLY":
                            data1 = cdf.variables[str(varNames[varN])][:,int(grdMODEL.indices[0,2]):int(grdMODEL.indices[0,3]),
                                                    int(grdMODEL.indices[0,0]):int(grdMODEL.indices[0,1])]
                            data2 = cdf.variables[str(varNames[varN])][:,int(grdMODEL.indices[1,2]):int(grdMODEL.indices[1,3]),
                                                    int(grdMODEL.indices[1,0]):int(grdMODEL.indices[1,1])]
                            
                        if type=="GLORYS2V1":
                            if var=='temperature': cdf=Dataset(getGLORYS2V1filename(year,ID,'T',dataPath))
                            if var=='salinity': cdf=Dataset(getGLORYS2V1filename(year,ID,'S',dataPath))
                            if var=='uvel': cdf=Dataset(getGLORYS2V1filename(year,ID,'U',dataPath))
                            if var=='vvel': cdf=Dataset(getGLORYS2V1filename(year,ID,'V',dataPath))
                            
                            data1 = np.squeeze(cdf.variables[str(varNames[varN])][0,:,int(grdMODEL.indices[0,2]):int(grdMODEL.indices[0,3]),
                                                    int(grdMODEL.indices[0,0]):int(grdMODEL.indices[0,1])])
                            data2 = np.squeeze(cdf.variables[str(varNames[varN])][0,:,int(grdMODEL.indices[1,2]):int(grdMODEL.indices[1,3]),
                                                    int(grdMODEL.indices[1,0]):int(grdMODEL.indices[1,1])])
                            
                            cdf.close()
                            
                        data = np.concatenate((data1,data2),axis=2)

                    else:
                        if type=="SODA":
                            data = cdf.variables[str(varNames[varN])][0,:,
                                                    int(grdMODEL.indices[0,2]):int(grdMODEL.indices[0,3]),
                                                    int(grdMODEL.indices[0,0]):int(grdMODEL.indices[0,1])]
                        if type=="SODAMONTHLY":
                            data = cdf.variables[str(varNames[varN])][:,int(grdMODEL.indices[0,2]):int(grdMODEL.indices[0,3]),
                                                    int(grdMODEL.indices[0,0]):int(grdMODEL.indices[0,1])]
                            
                        if type=="GLORYS2V1":
                            if var=='temperature': cdf=Dataset(getGLORYS2V1filename(year,ID,'T',dataPath))
                            if var=='salinity': cdf=Dataset(getGLORYS2V1filename(year,ID,'S',dataPath))
                            if var=='uvel': cdf=Dataset(getGLORYS2V1filename(year,ID,'U',dataPath))
                            if var=='vvel': cdf=Dataset(getGLORYS2V1filename(year,ID,'V',dataPath))
                            
                            data = np.squeeze(cdf.variables[str(varNames[varN])][0,:,int(grdMODEL.indices[0,2]):int(grdMODEL.indices[0,3]),
                                                    int(grdMODEL.indices[0,0]):int(grdMODEL.indices[0,1])])
                            
                            
                            cdf.close()
                
                if time==0 and var==vars[0]:
                    tmp=np.squeeze(data[0,:,:])
                    grdMODEL.mask = np.zeros((grdMODEL.lon.shape),dtype=np.float64)
                    grdMODEL.mask[:,:] = np.where(tmp==grdROMS.fill_value,1,0)


                """2D varibles"""
                if var=='ssh':
                    varN=2
                    print "TEST",var
                    SSHdata = np.zeros((indexROMS_SSH),dtype=np.float64)
                    if grdMODEL.splitExtract is True:
                        if type=="SODA":
                            data1 = cdf.variables[varNames[varN]][0,
                                                     int(grdMODEL.indices[0,2]):int(grdMODEL.indices[0,3]),
                                                     int(grdMODEL.indices[0,0]):int(grdMODEL.indices[0,1])]
                            data2 = cdf.variables[varNames[varN]][0,
                                                     int(grdMODEL.indices[1,2]):int(grdMODEL.indices[1,3]),
                                                     int(grdMODEL.indices[1,0]):int(grdMODEL.indices[1,1])]
                        if type=="SODAMONTHLY":
                            data1 = cdf.variables[str(varNames[varN])][int(grdMODEL.indices[0,2]):int(grdMODEL.indices[0,3]),
                                                    int(grdMODEL.indices[0,0]):int(grdMODEL.indices[0,1])]
                            data2 = cdf.variables[str(varNames[varN])][int(grdMODEL.indices[1,2]):int(grdMODEL.indices[1,3]),
                                                    int(grdMODEL.indices[1,0]):int(grdMODEL.indices[1,1])]
                            
                        if type=="GLORYS2V1":
                            cdf=Dataset(getGLORYS2V1filename(year,ID,'T',dataPath))
                           
                            data1 = np.squeeze(cdf.variables[str(varNames[varN])][0,int(grdMODEL.indices[0,2]):int(grdMODEL.indices[0,3]),
                                                    int(grdMODEL.indices[0,0]):int(grdMODEL.indices[0,1])])
                            data2 = np.squeeze(cdf.variables[str(varNames[varN])][0,int(grdMODEL.indices[1,2]):int(grdMODEL.indices[1,3]),
                                                    int(grdMODEL.indices[1,0]):int(grdMODEL.indices[1,1])])
                            
                            cdf.close()
                            
                        data = np.concatenate((data1,data2),axis=1)

                    else:
                        if type=="SODA":
                            data = cdf.variables[str(varNames[varN])][0,
                                                    int(grdMODEL.indices[0,2]):int(grdMODEL.indices[0,3]),
                                                    int(grdMODEL.indices[0,0]):int(grdMODEL.indices[0,1])]
                        if type=="SODAMONTHLY":
                            data = cdf.variables[str(varNames[varN])][int(grdMODEL.indices[0,2]):int(grdMODEL.indices[0,3]),
                                                    int(grdMODEL.indices[0,0]):int(grdMODEL.indices[0,1])]

                        if type=="GLORYS2V1":
                            cdf=Dataset(getGLORYS2V1filename(year,ID,'T',dataPath))
    
                            data = np.squeeze(cdf.variables[str(varNames[varN])][0,int(grdMODEL.indices[0,2]):int(grdMODEL.indices[0,3]),
                                                    int(grdMODEL.indices[0,0]):int(grdMODEL.indices[0,1])])
                            
                            cdf.close()
                if type=="GLORYS2V1":
                    
                    data=np.where(data<=-32.7,grdROMS.fill_value,data)
                    data=np.ma.masked_where(data<=grdROMS.fill_value,data)
                    
                """Take the input data and horizontally interpolate to your grid."""
                array1 = HorizontalInterpolation(var,grdROMS,grdMODEL,data,show_progress)
                   
                if var in ['temperature','salinity']:
                    STdata = VerticalInterpolation(var,array1,array1,grdROMS,grdMODEL)
                    print "Data range of %s after interpolation: %3.3f to %3.3f"%(varNames[varN],STdata.min(),STdata.max())
               
                    IOwrite.writeClimFile(grdROMS,time,climName,var,STdata)
                    if time==grdROMS.initTime and grdROMS.write_init is True:
                        IOinitial.createInitFile(grdROMS,time,initName,var,STdata)

                if var=='ssh':
                    SSHdata=array1[0,:,:]
                    print "Data range of %s after interpolation: %3.3f to %3.3f"%(varNames[varN],SSHdata.min(),SSHdata.max())
               
                    IOwrite.writeClimFile(grdROMS,time,climName,var,SSHdata)
                    if time==grdROMS.initTime:
                        IOinitial.createInitFile(grdROMS,time,initName,var,SSHdata)

                if var=='uvel':
                    array2=array1

                if var=='vvel':

                    UBARdata = np.zeros((indexROMS_UBAR),dtype=np.float64)
                    VBARdata = np.zeros((indexROMS_VBAR),dtype=np.float64)

                    urot,vrot = rotate(grdROMS,grdMODEL,data,array2,array1)

                    u,v = interpolate2UV(grdROMS,grdMODEL,urot,vrot)

                    Udata,Vdata,UBARdata,VBARdata = VerticalInterpolation(var,u,v,grdROMS,grdMODEL)

                if var=='vvel':
                    print "Data range of U after interpolation: %3.3f to %3.3f - V after scaling: %3.3f to %3.3f"%(Udata.min(),Udata.max(),Vdata.min(),Vdata.max())
               
                    IOwrite.writeClimFile(grdROMS,time,climName,var,Udata,Vdata,UBARdata,VBARdata)
                    if time==grdROMS.initTime:
                        """We print time=initTime to init file so that we have values for ubar and vbar (not present at time=1)"""
                        IOinitial.createInitFile(grdROMS,time,initName,var,Udata,Vdata,UBARdata,VBARdata)
            if type!='GLORYS2V1':
                cdf.close()
            if show_progress is True:
                from progressBar import progressBar
                # find unicode characters here: http://en.wikipedia.org/wiki/List_of_Unicode_characters#Block_elements
                empty  =u'\u25FD'
                filled =u'\u25FE'

                progress = progressBar(color='green',width=30, block=filled.encode('UTF-8'), empty=empty.encode('UTF-8'))
                message='Finished conversions for time %s'%(grdROMS.message)
                progress.render(100,message)
            else:
                message='Finished conversions for time %s'%(grdROMS.message)
                
            time+=1
