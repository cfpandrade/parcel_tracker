# 📦 Parcel Tracker - Home Assistant Integration

[![Open your Home Assistant instance and show the add-on repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cfpandrade&repository=parcel_tracker&category=integration)

A custom Home Assistant integration for tracking packages from multiple carriers directly in your Home Assistant dashboard.

---

## 🚀 Installation via HACS

This integration is **not yet available in the default HACS store**, so you need to **add it manually** as a custom repository.

### **1️⃣ Add the Repository to HACS**
1. Open **Home Assistant** and go to **HACS**.
2. Click on **Integrations**.
3. Click the **three-dot menu** (top-right) and select **Custom repositories**.
4. In the **Repository URL** field, enter:  https://github.com/cfpandrade/parcel_tracker
5. Set the **category** to **Integration** and click **Add**.
6. Refresh HACS and search for **Parcel Tracker** under "Integrations".

---

### **2️⃣ Install the Integration**
1. In **HACS → Integrations**, search for **Parcel Tracker**.
2. Click **Download** and install it.
3. **Restart Home Assistant** once the installation is complete.

---

### **3️⃣ Configure the Integration**
1. Go to **Settings → Devices & Services**.
2. Click **Add Integration** and search for **Parcel Tracker**.
3. Follow the setup wizard to link your package tracking accounts.

---

## ⚡ Features
- 📍 **Real-time tracking** of packages from multiple carriers.
- 🔔 **Home Assistant notifications** for delivery updates.
- 📊 **Lovelace card support** for visualizing shipments.
- 🌎 **Multi-carrier support** (add details here if needed).

---

## 🛠 Manual Installation (Without HACS)
If you prefer a **manual installation**, follow these steps:

1. Download the latest release from GitHub: https://github.com/cfpandrade/parcel_tracker
2. 2. Copy the `parcel_tracker` folder to: /config/custom_components/parcel_tracker/
3. Restart Home Assistant.
4. Add the integration in **Settings → Devices & Services**.

---

## 📝 Support & Feedback
If you encounter issues or have feature requests, please open an [issue on GitHub](https://github.com/cfpandrade/parcel_tracker/issues).

---

## 📜 License
This project is licensed under the **MIT License**.

