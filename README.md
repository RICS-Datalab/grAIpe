# API for Orthophoto and Index Calculation

This API is designed to work on top of the webODM API and provides functionalities to calculate orthophotos and indexes. It leverages the capabilities of webODM to process aerial imagery and generate accurate georeferenced outputs.

## Features

Orthophoto Generation: The API allows users to submit aerial images for processing and obtain orthophotos, which are geometrically corrected, true-to-scale images with uniform scale and minimal distortion.

Index Calculation: The API supports the calculation of various indexes such as NDVI (Normalized Difference Vegetation Index), NDWI (Normalized Difference Water Index), and many more. These indexes provide valuable information about vegetation health, water presence, and other environmental characteristics.

Flexible Input Formats: The API accepts a wide range of aerial image formats, including JPEG, TIFF, and more. It ensures compatibility with various aerial data sources and simplifies the integration process.

API Integration: Developers can easily integrate this API into their own applications, websites, or systems. The API follows RESTful principles, providing simple and intuitive endpoints for seamless integration.

## Requirements

To use this API, you will need to install the following applications (if they are not installed already):

  - [Git](https://git-scm.com/downloads)
  - [Docker](https://www.docker.com/)
  - [Docker-compose](https://docs.docker.com/compose/install/)
  - Python
  - Pip
-Windows users should install Docker Desktop and 
  1) make sure Linux containers are enabled (Switch to Linux Containers...), 
  2) give Docker enough CPUs (default 2) and RAM (>4Gb, 16Gb better but leave some for Windows) by going to Settings -- Advanced, and 
  3) select where on your hard drive you want virtual hard drives to reside (Settings -- Advanced -- Images & Volumes).

## Installation

2.  Clone the repository to your local machine
From the Docker Quickstart Terminal or Git Bash (Windows), or from the command line (Mac / Linux), type:
```bash
    git clone https://github.com/RICS-Datalab/grAIpe
    cd grAIpe
    ./graipe.sh
``` 
3. Install the required dependencies:

```bash
    cd your-api-repo
    npm install
```
4. Configure API Credentials:

    Update the configuration file (config.js or .env) with your webODM API credentials. Provide the necessary information such as the API endpoint URL, API key, or access tokens.

5. Start the API server:


## API Endpoints

The API provides the following endpoints for interacting with the orthophoto and index calculation functionalities:

`POST` /api/login: Submit aerial images for orthophoto generation.

`POST` /api/create_project/{name}

`GET` /api/list_projects

`POST` /api/create_execute_task/{project}

`GET` /api/download/{project}/{task}/{file}

`POST` /api/index/{project}/{task}/{index}

`GET` /api/dsm_dtm_chm/{project}/{task}/{file}

`GET` /api/full/{project}/{task}/{index}

Please refer to the API documentation for detailed information on request/response formats and example usage.

## Contributing

Contributions are welcome! If you encounter any issues or have suggestions for improvement, please feel free to submit bug reports or pull requests.


## License

This project is licensed under the [MIT License]().
