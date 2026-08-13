# Host dashboard prototype integration

The Calendar route is based on `nicer.homes_design_system/ui_kits/host-dashboard/Pricing.jsx` and `App.jsx`. The prototype layout, drawers, controls, tooltip, range selection, and design tokens are kept as the UI source of truth.

The production adapter currently replaces only the prototype's listing/date/price data and the actions that already have backend endpoints:

- `GET /api/pricing-calendar` supplies properties, dates, current prices, recommendations, and availability.
- `POST /api/imports/hostex/booking-site` powers **Fetch current prices**.
- `POST /api/pricing/run` powers **Generate price recommendations**.
- `POST /api/pricing/publish` powers **Apply prices**.

Prototype interactions without a stable backend contract remain local prototype state for now (settings forms, range price editing, and competitor refresh). They are intentionally not redesigned or extended; they are documented here until their API contracts are finalized.
