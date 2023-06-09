import rasterio
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import io
import base64

"""
    This function loads the orthophoto from disk and returns the bands as numpy arrays.
    The bands are normalized by default.
    The bands are returned in the following order: band1, band2, band3, band4, band5, band6, band7, band8

    Parameters
    ----------
    normalize : bool
        If true, the bands are normalized. Default is True.

    Returns
    -------
    band1_norm : numpy array
        The Blue band
    band2_norm : numpy array
        The Green band 
    band3_norm : numpy array
        The Red band 
    band4_norm : numpy array
        The NIR band
    band5_norm : numpy array
        The Red Edge band
    band6 : numpy array
        Empty Band
    band7_norm : numpy array
        The computed Index band
    band8 : numpy array
        The Canopy Height Model (CHM)
    
    Examples
    --------
    >>> band1_norm, band2_norm, band3_norm, band4_norm, band5_norm, band6, band7_norm, band8 = load_orthophoto_from_disk()

"""


# TODO: change from hard-coded path to ENV variable
# Step 1: Data Preprocessing
def load_orthophoto_from_disk(path: str = "./final.tif", normalize: bool = True):
    # Open the image
    with rasterio.open(path) as src:
        # Read the bands into separate variables
        band1, band2, band3, band4, band5, band6, band7, band8 = src.read()

        if normalize:
            # Normalize the bands
            band1_norm = band1 / 65535
            band2_norm = band2 / 65535
            band3_norm = band3 / 65535
            band4_norm = band4 / 65535
            band5_norm = band5 / 65535
            band7_norm = band5 / 65535
            return (
                band1_norm,
                band2_norm,
                band3_norm,
                band4_norm,
                band5_norm,
                band6,
                band7_norm,
                band8,
            )

        return band1, band2, band3, band4, band5, band6, band7, band8

    return None


""" 
    This function extracts the features from the bands and returns them as numpy arrays.
    The features are returned in the following order: rgb, ndvi, savi

    Parameters
    ----------
    bands : list
        The list of bands returned by load_orthophoto_from_disk()

    Returns
    -------
    rgb : numpy array
        The RGB image
    ndvi : numpy array
        The NDVI image
    ndvi : numpy array
        The SAVI image

    Examples
    --------
    >>> rgb, ndvi = extract_features(bands)

"""


# Step 2: Feature Extraction
def extract_features(bands: list):
    # Unpack the bands from the list
    (
        band1_norm,
        band2_norm,
        band3_norm,
        band4_norm,
        band5_norm,
        band6,
        band7_norm,
        band8,
    ) = bands
    # Compute RGB (camera was an Altum sensor?)
    rgb = np.dstack((band3_norm, band2_norm, band1_norm))
    # Compute NDVI (camera was an Altum sensor?)
    # NDVI = (NIR - Red) / (NIR + Red)
    ndvi = (band4_norm - band3_norm) / (band4_norm + band3_norm)
    ## SAVI (Soil Adjusted Vegetation Index)
    # SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)
    L = 0.8
    savi = ((band4_norm - band3_norm) / (band4_norm + band3_norm + L)) * (1 + L)

    return rgb, ndvi, savi


"""
    This function segments the NDVI image using KMeans clustering and returns the segmented image as a numpy array.

    Parameters
    ----------
    ndvi : numpy array
        The NDVI image
    k : int
        The number of clusters to use for KMeans clustering. Default is 5.

    Returns
    -------
    labels : numpy array
        The segmented image

    Examples
    --------
    >>> labels = segment_image_with_clustering(ndvi, k=5)

"""


def segment_image_with_clustering(feature_image: np.array, k: int = 5):
    # remove nan values from feature_image
    clean_feature_image = np.nan_to_num(feature_image)
    # Flatten the NDVI array to 1D array, as required for scikit-learn
    flattened_feature_image = clean_feature_image.flatten().reshape(-1, 1)
    # Step 3: Unsupervised Learning
    # Perform KMeans clustering (change n_clusters as necessary)
    kmeans = KMeans(n_clusters=k).fit(flattened_feature_image)
    # Reshape the labels to the original image shape
    labels = kmeans.labels_.reshape(feature_image.shape)

    return labels


"""
    This function prepares the response to be sent back to the client.

    Parameters
    ----------
    labels : numpy array
        The segmented image
    cmap : matplotlib colormap
        The colormap to use for the segmented image. Default is 'RdYlGn'.

    Returns
    -------
    response : dict
        The response to be sent back to the client

    Examples
    --------
    >>> response = prepare_response(labels)

"""


def prepare_response(labels: np.array, cmap=cm.get_cmap("RdYlGn")):
    # Create a figure and axis
    fig, ax = plt.subplots()

    # Set the colormap to 'RdYlGn' and display the NDVI image
    im = ax.imshow(labels, cmap=cmap)

    # Remove the axis labels and ticks
    ax.axis("off")

    # Create an in-memory byte stream
    image_stream = io.BytesIO()

    # Save the image to the byte stream in JPEG format
    plt.savefig(
        image_stream, format="jpeg", transparent=True, dpi=300, bbox_inches="tight"
    )

    # Get the byte stream value
    image_bytes = image_stream.getvalue()

    # Encode the image bytes as base64
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    return {"image": base64_image}
