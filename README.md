# Parcel Tracker 📦

Parcel Tracker is a custom Home Assistant integration that allows you to track your parcel deliveries using the Parcel API. This integration periodically polls the Parcel API to update the delivery status and displays the information in Home Assistant as a sensor.

## Features

- **Real-time Tracking:** Displays up-to-date delivery status and expected delivery dates.
- **Configurable:** Easily set up via the Home Assistant UI.
- **Detailed Delivery Data:** Shows tracking number, description, carrier, status (e.g., Delivered, In Transit), and expected date.
- **Multilingual Feedback:** Provides error messages in Spanish to guide configuration.

## Installation

### Prerequisites

- Home Assistant installed and running.
- A valid API key from [Parcel API](https://api.parcel.app).

### Manual Installation

1. Copy the `parcel_tracker` folder into your Home Assistant `custom_components` directory.
2. Restart Home Assistant to load the new integration.

### HACS Installation

If you use HACS (Home Assistant Community Store):

1. Add this repository URL to HACS.
2. Install the integration via HACS.
3. Restart Home Assistant.

## Configuration

After installation, set up the integration through Home Assistant's UI:

1. Go to **Configuration > Integrations**.
2. Click on **Add Integration** and search for "Parcel Tracker 📦".
3. Enter your Parcel API key when prompted.
4. The configuration flow validates your API key and sets up the sensor.

> **Note:** Error messages during configuration are in Spanish. For example, if an invalid API key is entered, you might see "Clave API inválida (401 Unauthorized)".

## Usage

Once configured, the integration creates a sensor (e.g., `sensor.parcel_tracker`) that displays:
- **State:** "Updated" when data is fetched successfully, or an error message if something goes wrong.
- **Extra Attributes:** A list of delivery details including tracking numbers, descriptions, carrier codes, delivery statuses, and expected dates.

The available delivery statuses include:
- Delivered
- Frozen
- In Transit
- Awaiting Pickup
- Out for Delivery
- Not Found
- Failed Attempt
- Delivery Exception
- Info Received

## Troubleshooting

- **Invalid API Key:**  
  If you receive errors like "Clave API inválida (401 Unauthorized)", verify that your API key is correct.

- **Network Issues:**  
  Ensure that your Home Assistant instance has internet access and that the Parcel API is reachable.

- **Logs:**  
  Check Home Assistant logs for detailed error messages if the sensor state indicates an issue (e.g., "API Error", "Network Error", or "Unknown Error").

## Contributing

Contributions, bug reports, and feature requests are welcome! Feel free to open an issue or submit a pull request on the [GitHub repository](https://github.com/cfpandrade/parcel_tracker).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Thanks to the Parcel API team for providing a robust API for tracking deliveries.
- Developed by [cfpandrade](https://github.com/cfpandrade).
