from __future__ import annotations

# External Imports
import numpy as np
import rasterio as rio
from typing import Optional, Dict, List
from copy import deepcopy


class Dataset:
    profile: rio.profiles.Profile
    bands: Dict[str, np.ndarray]
    nodata: Optional[object]
    meta: Optional[dict]
    subdatasets: Optional[List[Dataset]]

    def __init__(self, profile: rio.profiles.Profile, bands: Dict[str, np.ndarray], nodata: Optional[object] = None,
                 meta: Optional[dict] = None, subdatasets: Optional[List[Dataset]] = None):
        """Instantiate a Dataset object

        :param profile: Profile of the dataset
        :param bands: A dictionary containing the band data associated with keys
        :param nodata: The type/value used to denote no or invalid data
        :param meta: (Optional) A dictionary containing metadata about the dataset
        :param subdatasets: (Optional) A list containing additional subdataset Dataset objects
        """

        self.profile = profile
        self.bands = bands
        self.nodata = nodata
        self.meta = meta
        self.subdatasets = subdatasets


def combine(first: Dataset, second: Dataset, skip_duplicates: Optional[bool] = False) -> Dataset:
    """Combine one dataset with another compatible dataset

    This function simply checks for basic compatibility (resolution, array size,
    etc.) and then combines the list of bands. Also note that the function
    makes a deep copy of both datasets so a clean output can be created. This
    leads to a possible ballooning in memory!

    :param first: The dataset that the second will be combined into
    :param second: The dataset that will be combined with the first
    :param skip_duplicates: (Optional) Whether or not to skip duplicate bands (Default False)
    :return: This dataset with the new dataset added
    """

    # Combination with "None" should return the original
    if first is None:
        return second

    if second is None:
        return first

    # Check for compatibility
    # [TODO] Dataset combination checks need to be much more thorough
    # [FIXME] Current combine implementation doesn't actually catch different-dimension ndarrays!
    if first.meta["resolution"] != second.meta["resolution"] or \
            first.profile["crs"] != second.profile["crs"] or \
            first.profile["height"] != second.profile["height"] or \
            first.profile["width"] != second.profile["width"]:
        raise RuntimeError("Tried to combine two datasets that are not compatible!")

    # Create a deep copy of datasets (Caution, EXPENSIVE!)
    # [TODO] Make clean combination of datasets less resource-intensive
    first_bands = deepcopy(first.bands)
    second_bands = deepcopy(second.bands)

    # Test for bands with the same name to avoid overwriting data
    # If the user wants to skip duplicates, remove the duplicate entry from the second
    # band dictionary.
    for key in first_bands.keys():
        if key in second_bands.keys():
            if not skip_duplicates:
                raise RuntimeError("Tried to combine two datasets with matching band keys!")
            else:
                del second_bands[key]

    # Actually copy over
    first.bands = {**first_bands, **second_bands}

    # Create a deep copy of all the subdatasets (Caution, potentially EXTREMELY EXPENSIVE!)
    first_subdatasets = deepcopy(first.subdatasets) if first.subdatasets is not None else {}
    second_subdatasets = deepcopy(second.subdatasets) if second.subdatasets is not None else {}

    # Combine list of subdatasets
    first.subdatasets = {**first_subdatasets, **second_subdatasets}

    # Return the first dataset with the second copied into it
    return first
