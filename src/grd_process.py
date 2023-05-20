"""GRD SAR files processing"""
from typing import Optional, List
from pyroSAR import identify
from pyroSAR.auxdata import dem_autoload
from spatialist import Vector
from pyroSAR.snap import geocode, gpt

import os
import shutil
import geopandas as gpd
from Sentinel_SAR.src.data import OilTerminals

import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

class sar_processing:
    """SAR data processing"""

    @staticmethod
    def remove_files(folder_path:str = None)-> None:
        """Remove all files in a folder"""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        else:
            for file in os.listdir(folder_path):
                if os.path.isfile(os.path.join(folder_path, file)):
                    os.remove(os.path.join(folder_path, file))
                else:
                    shutil.rmtree(os.path.join(folder_path, file))
     
    def __init__(
            self,
            sar_zip_file:str = None,
            location_name:str = None) -> None:
        self.sar_zip_file = sar_zip_file
        self.location_name = location_name
    
    def location_wkt(self)-> None:
        """Getting the Polygon of oil terminal location"""
        terminals = OilTerminals()
        data_dict = terminals.read_data()
        data_dict = terminals.wkt_polygon()
        self.poly = data_dict[self.location_name]

    def naming(self):
        """Identifying SAR file, if printed gives description"""
        self.id = identify(self.sar_zip_file)
        return self.id
    
    def get_orbit_file(self)-> None:
        """Getting the Orbit file"""
        osvdir = '.snap/auxdata/Orbits/Sentinel-1/'
        osvdir = os.path.join(os.path.expanduser('~'), osvdir)
        try:
            os.path.exists(osvdir)
            self.orbit_path = self.id.getOSV(osvdir = osvdir, osvType='POE', returnMatch=True)
        except Exception:
            logging.debug("Make sure to install ESA SNAP")
            logging.debug("https://step.esa.int/main/download/snap-download/")
    
    def dem_file(self)-> None:
        """Auto-loading DEM file"""
        # Creating Shape file
        gdf = gpd.GeoDataFrame(geometry=[self.poly])
        gdf.crs = 'EPSG:4326'
        shp_dir = f'data/shp/{self.location_name}'

        self.remove_files(shp_dir)
        
        shp_file = os.path.join(shp_dir, f'{self.location_name}.shp')
        gdf.to_file(shp_file, driver='ESRI Shapefile')

        # DEM auto loading
        with Vector(shp_file) as vec:
            vrt = dem_autoload(geometries=[vec],
                            demType='SRTM 1Sec HGT',
                            buffer=0.1)
            
    def pol_stamp(self)-> None:
        """Getting the polarization of SAR file"""
        self.file_name = os.path.basename(self.sar_zip_file)
        self.uuid = self.file_name.split('.')[0]
        self.polstamp = self.uuid.split("_")[3]
        self.polarization = self.polstamp[2:4]         
        print(self.polarization)
        if self.polarization == 'DV':
            self.pols = ['VH','VV']
        elif self.polarization == 'DH':
            self.pols = ['HH','HV']
        elif self.polarization == 'SH' or self.polarization == 'HH':
            self.pols = ['HH']
        elif self.polarization == 'SV':
            self.pols = ['VV']
        else:
            self.pols = None
            logging.error("Polarization error!")
        
        if not self.pols is None:
            logging.info(f"Product {self.uuid} is of polarisation {self.pols}")
        return self.pols
    
    def snap_process(
            self,
            out_dir:str = 'data/processed',
            shp_file:str = 'data/shp',
            polarization: str = None)-> None:
        """SAR data pre-processing with pyoSAR
        
            Args:
                out_dir: Directory for the processed files
                shp_file: Directory where the files needed to be saved
                polarization: Polarizations need to be processed
        """
        # Setting the output Directory for processed files
        out_dir = os.path.join(out_dir, self.location_name)
        self.remove_files(out_dir)

        # Getting the Shape files
        shp_file = os.path.join(shp_file, self.location_name)
        shp_file = os.path.join(shp_file, f'{self.location_name}.shp')

        # Performing the default SAR processing from PyroSAR python package
        # https://pyrosar.readthedocs.io/en/latest/index.html
        if polarization in self.pols:
            logging.info(f"SAR-Processing for {self.uuid}, polarisation - {polarization}")
            geocode(
                infile = self.sar_zip_file,
                outdir = out_dir,
                shapefile = shp_file,
                polarizations = polarization,
                imgResamplingMethod = 'BILINEAR_INTERPOLATION',
                speckleFilter = 'Refined Lee',
                refarea = 'sigma0',
                returnWF = True)
            logging.info("SAR-Processing finished!")
        else:
            logging.debug(f"Polarization: {polarization} is not of the SAR file {self.file_name}")
            logging.debug(f"Select polarisation from these: {self.pols}")
        
if __name__ == "__main__":
    sar_zip_file_folder = 'downloads/S1_data/'
    sar_zip_file_folder = os.path.join(os.path.expanduser('~'), sar_zip_file_folder)
    files = os.listdir(sar_zip_file_folder)
    for file in files:
        sar_zip_file = os.path.join(sar_zip_file_folder, file)
    location_name = 'stanlow'

    sar = sar_processing(
        sar_zip_file,
        location_name)
    sar.location_wkt()
    sar.naming()
    sar.get_orbit_file()
    sar.dem_file()
    sar.pol_stamp()
    sar.snap_process(polarization = 'VH')