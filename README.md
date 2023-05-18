# API for Orthophoto and Index Calculation

This API is designed to work on top of the webODM API and provides functionalities to calculate orthophotos and indexes. It leverages the capabilities of webODM to process aerial imagery and generate accurate georeferenced outputs.

## Features

Orthophoto Generation: The API allows users to submit aerial images for processing and obtain orthophotos, which are geometrically corrected, true-to-scale images with uniform scale and minimal distortion.

Index Calculation: The API supports the calculation of various indexes such as NDVI (Normalized Difference Vegetation Index), NDWI (Normalized Difference Water Index), and many more. These indexes provide valuable information about vegetation health, water presence, and other environmental characteristics.

Flexible Input Formats: The API accepts a wide range of aerial image formats, including JPEG, TIFF, and more. It ensures compatibility with various aerial data sources and simplifies the integration process.

API Integration: Developers can easily integrate this API into their own applications, websites, or systems. The API follows RESTful principles, providing simple and intuitive endpoints for seamless integration.

## Requirements

To use this API, you will need the following:

webODM: Make sure you have a running instance of webODM, accessible via API endpoints.

Aerial Images: Prepare the aerial images you wish to process in an appropriate format, supported by webODM.

API Credentials: Obtain the necessary credentials (API key, tokens, etc.) to authenticate requests to the webODM API.

## Installation

1.  Clone the repository to your local machine:
```bash
    git clone https://github.com/OpenDroneMap/WebODM --config core.autocrlf=input --depth 1
    cd WebODM
    ./webodm.sh start 
``` 
2. Install the required dependencies:

```bash
    cd your-api-repo
    npm install
```
3. Configure API Credentials:

    Update the configuration file (config.js or .env) with your webODM API credentials. Provide the necessary information such as the API endpoint URL, API key, or access tokens.

4. Start the API server:


## API Endpoints

The API provides the following endpoints for interacting with the orthophoto and index calculation functionalities:

    POST /api/orthophoto: Submit aerial images for orthophoto generation.

    GET /api/orthophoto/:id: Get the status and download links for a specific orthophoto job ID.

    POST /api/index: Calculate an index for a given orthophoto.

    GET /api/index/:id: Get the status and download links for a specific index calculation job ID.

Please refer to the API documentation for detailed information on request/response formats and example usage.

## Contributing

Contributions are welcome! If you encounter any issues or have suggestions for improvement, please feel free to submit bug reports or pull requests.


## License

This project is licensed under the [MIT License]().