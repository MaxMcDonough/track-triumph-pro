# Architecture

- Serve the existing static frontend with Vite using `frontend` as its root; this preserves the existing HTML page URLs without requiring a separate persistent server.
- Include every frontend HTML page as a build entry; this keeps business, CRM, documentation, and nested pages available after publishing.