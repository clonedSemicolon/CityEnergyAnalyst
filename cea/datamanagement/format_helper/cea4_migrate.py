"""
Mirgate the format of the input data to CEA-4 format after verification.

"""

import cea.inputlocator
import os
import cea.config
import time
import pandas as pd
import geopandas as gpd


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.datamanagement.format_helper.cea4_verify import cea4_verify, verify_shp, verify_file_exists, verify_csv
from cea.utilities.dbf import dbf_to_dataframe


## --------------------------------------------------------------------------------------------------------------------
## The paths to the input files for CEA-3
## --------------------------------------------------------------------------------------------------------------------

# The paths are relatively hardcoded for now without using the inputlocator script.
# This is because we want to iterate over all scenarios, which is currently not possible with the inputlocator script.
def path_to_input_file_without_db_3(scenario, item):

    if item == "zone":
        path_to_input_file = os.path.join(scenario, "inputs", "building-geometry", "zone.shp")
    elif item == "surroundings":
        path_to_input_file = os.path.join(scenario, "inputs", "building-geometry", "surroundings.shp")
    elif item == "air_conditioning":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "air_conditioning.dbf")
    elif item == "architecture":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "architecture.dbf")
    elif item == "indoor_comfort":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "indoor_comfort.dbf")
    elif item == "internal_loads":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "internal_loads.dbf")
    elif item == "supply_systems":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "supply_systems.dbf")
    elif item == "typology":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "typology.dbf")
    elif item == 'streets':
        path_to_input_file = os.path.join(scenario, "inputs", "networks", "streets.shp")
    elif item == 'terrain':
        path_to_input_file = os.path.join(scenario, "inputs", "topography", "terrain.tif")
    elif item == 'weather':
        path_to_input_file = os.path.join(scenario, "inputs", "weather", "weather.epw")

    return path_to_input_file


## --------------------------------------------------------------------------------------------------------------------
## Helper functions
## --------------------------------------------------------------------------------------------------------------------
def replace_shapefile_dbf(scenario, item, new_dataframe, list_attributes_3):
    """
    Replace the DBF file of a shapefile with the contents of a new DataFrame,
    ensuring matching of `['Name']` in the shapefile and `['name']` in the new DataFrame.

    :param shapefile_path: Path to the shapefile (without file extension).
    :param new_dataframe: pandas DataFrame with the new data to replace the DBF file.
    """
    # Load the original shapefile
    shapefile_path = path_to_input_file_without_db_3(scenario, item)
    gdf = gpd.read_file(shapefile_path)
    list_attributes_3_without_name = [item for item in list_attributes_3 if item != 'name']
    gdf = gdf.drop(columns=list_attributes_3_without_name, errors='ignore')

    # Perform an inner join to match rows based on ['Name'] and ['name']
    merged = gdf.merge(new_dataframe, how='outer', left_on='Name', right_on='name')

    # Ensure all geometries are preserved
    if len(merged) != len(gdf):
        raise ValueError("Not all rows in the GeoDataFrame have a matching entry in the new DataFrame.")

    # Drop duplicate or unnecessary columns, keeping only the new attributes
    new_gdf = merged.drop(columns=['Name'], errors='ignore')

    # Save the updated shapefile
    new_gdf.to_file(shapefile_path, driver="ESRI Shapefile")


## --------------------------------------------------------------------------------------------------------------------
## Migrate to CEA-4 format from CEA-3 format
## --------------------------------------------------------------------------------------------------------------------

def migrate_cea3_to_cea4(scenario):

    # Create the list of items that has been changed from CEA-3 to CEA-4
    list_items_changed = ['zone', 'surroundings',
                          'air_conditioning', 'architecture', 'indoor_comfort', 'internal_loads', 'supply_systems',
                          'typology']
    dict_missing = cea4_verify(scenario)

    #0. get the scenario name
    scenario_name = os.path.basename(scenario)

    #1. about zone.shp and surroundings.shp
    COLUMNS_ZONE_3 = ['Name', 'floors_bg', 'floors_ag', 'height_bg', 'height_ag']
    COLUMNS_TYPOLOGY_3 = ['Name', 'YEAR', 'STANDARD', '1ST_USE', '1ST_USE_R', '2ND_USE', '2ND_USE_R', '3RD_USE', '3RD_USE_R']
    COLUMNS_SURROUNDINGS_3 = ['Name', 'height_ag', 'floors_ag']
    columns_mapping_dict_name = {'Name': 'name'}
    columns_mapping_dict_typology = {'YEAR': 'year',
                                     'STANDARD': 'const_type',
                                     '1ST_USE': 'use_type1',
                                     '1ST_USE_R': 'use_type1r',
                                     '2ND_USE': 'use_type2',
                                     '2ND_USE_R': 'use_type2r',
                                     '3RD_USE': 'use_type3',
                                     '3RD_USE_R': 'use_type3r'
                                     }

    list_missing_files_shp_building_geometry = dict_missing.get('building-geometry')
    list_missing_files_typology = verify_file_exists(scenario, ['typology'])
    list_missing_attributes_zone_4 = dict_missing.get('zone')
    list_missing_attributes_surroundings_4 = dict_missing.get('surroundings')

    if 'zone' not in list_missing_files_shp_building_geometry:
        list_missing_attributes_zone_3 = verify_shp(scenario, 'zone', COLUMNS_ZONE_3)
        if not list_missing_attributes_zone_3 and list_missing_attributes_zone_4:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'zone.shp follows the CEA-3 format.')
            zone_df_3 = gpd.read_file(path_to_input_file_without_db_3(scenario, 'zone'))
            zone_df_3.rename(columns=columns_mapping_dict_name, inplace=True)
            if 'typology' not in list_missing_files_typology:
                list_missing_attributes_typology_3 = verify_csv(scenario, 'typology', COLUMNS_TYPOLOGY_3)
                if not list_missing_attributes_typology_3 and list_missing_attributes_zone_4:
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'typology.shp follows the CEA-3 format.')
                    typology_df = dbf_to_dataframe(path_to_input_file_without_db_3(scenario, 'typology'))
                    typology_df.rename(columns=columns_mapping_dict_typology, inplace=True)
                    zone_df_4 = pd.merge(zone_df_3, typology_df, left_on=['name'], right_on=["Name"], how='left')
                    zone_df_4.drop(columns=['Name'], inplace=True)

                    # Replace, and remove.
                    replace_shapefile_dbf(scenario, 'zone', zone_df_4, COLUMNS_ZONE_3)
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'CEA-3 zone.shp and typology.dbf have been merged and migrated to CEA-4 format.')
                    os.remove(path_to_input_file_without_db_3(scenario, 'typology'))
                    print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'CEA-3 zone.shp has been removed.')
                else:
                    raise ValueError('For Scenario: {scenario}, '.format(scenario=scenario_name), 'typology.shp does not follow the CEA-3 format. CEA cannot proceed with migration.')
        elif list_missing_attributes_zone_3 and not list_missing_attributes_zone_4:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'zone.shp already follows the CEA-4 format.')
        else:
            raise ValueError('For Scenario: {scenario}, '.format(scenario=scenario_name), 'zone.shp follows neither the CEA-3 nor CEA-4 format. CEA cannot proceed with the data migration.')

    if 'surroundings' not in list_missing_files_shp_building_geometry:
        list_missing_attributes_surroundings_3 = verify_shp(scenario, 'surroundings', COLUMNS_SURROUNDINGS_3)
        if not list_missing_attributes_surroundings_3 and list_missing_attributes_surroundings_4:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'surroundings.shp follows the CEA-3 format.')
            surroundings_df_3 = gpd.read_file(path_to_input_file_without_db_3(scenario, 'surroundings'))
            surroundings_df_4 = surroundings_df_3.rename(columns=columns_mapping_dict_name, inplace=True)
            replace_shapefile_dbf(scenario, 'surroundings', surroundings_df_4, COLUMNS_SURROUNDINGS_3)

        elif list_missing_attributes_surroundings_3 and not list_missing_attributes_surroundings_4:
            print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'surroundings.shp already follows the CEA-4 format.')
        else:
            raise ValueError('For Scenario: {scenario}, '.format(scenario=scenario_name), 'surroundings.shp follows neither the CEA-3 nor CEA-4 format. CEA cannot proceed with the data migration.')
