"""GRD SAR files processing"""
from pyroSAR import identify
from pyroSAR.auxdata import dem_autoload
from spatialist import Vector
from pyroSAR.snap import geocode, gpt

import geopandas as gpd
from Sentinel_SAR.src.data import OilTerminals

import logging
# basic info with some message filtering
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

class sar_processing:
    terminals = OilTerminals()
    data_dict = terminals.read_data()
    data_dict = terminals.wkt_polygon()

    filename = 'flotta'
    poly = data_dict["flotta"]

    def __init__(
            self,
            sar_zip_file:str = None) -> None:
        self.sar_zip_file = sar_zip_file

    def naming(self)->None:
        self.id = identify(self.sar_zip_file)
    
    def get_orbit_file(self)-> None:
        self.orbit_path = self.id.getOSV(osvdir='/home/vardh/.snap/auxdata/Orbits/Sentinel-1/', osvType='POE', returnMatch=True)
    
    def dem_file(self)-> None: 
        gdf = gpd.GeoDataFrame(geometry=[self.poly])
        gdf.crs = 'EPSG:4326'
        output_file = 'data/shp/flotta/flotta.shp'
        gdf.to_file(output_file, driver='ESRI Shapefile')

        with Vector(output_file) as vec:
            vrt = dem_autoload(geometries=[vec],
                            demType='SRTM 1Sec HGT',
                            buffer=0.1)

    def snap_process(
            self,
            out_dir:str = None,
            shp_file:str = None)-> None:
        geocode(
            infile = self.sar_zip_file,
            outdir = out_dir,
            shapefile = shp_file,
            polarizations = 'VV',
            imgResamplingMethod = 'BILINEAR_INTERPOLATION',
            speckleFilter = 'Refined Lee',
            refarea = 'sigma0',
            returnWF = True)
        
if __name__ == "__main__":
    sar_zip_file = '/home/vardh/apps/tmp/S1A_IW_GRDH_1SDV_20230313T175210_20230313T175235_047629_05B868_4E5C.zip'
    out_dir = 'data/pre_process/graphs'
    shp_file = 'data/shp/flotta/flotta.shp'
    sar = sar_processing(sar_zip_file)
    sar.naming()
    sar.get_orbit_file()
    sar.dem_file()
    sar.snap_process(
        out_dir = out_dir)