  ---
  
  # Parcel Tracker
  
  Parcel Tracker is a custom component for Home Assistant that allows tracking of packages from multiple carriers.
  
  ## Features
  - Track your Amazon, AnPost, DPD, UPS, and other shipments.
  - Get real-time updates on delivery status.
  - Automatically calculates days until delivery if applicable.
  
  ## Installation
  1. Copy the `custom_components/parcel_tracker/` folder to your Home Assistant `custom_components/` directory.
  2. Restart Home Assistant.
  3. Add the integration via **Settings > Devices & Services > Add Integration** and enter your API details.
  
  ## Configuration
  After installation, you need to provide:
  - **API URL** from ParcelApp.
  - **Authentication Token** to fetch tracking data.
  
  ## Support
  For issues or feature requests, visit the [GitHub repository](https://github.com/cfpandrade/parcel_tracker/issues).
  
  ## License
  This project is licensed under the MIT License.