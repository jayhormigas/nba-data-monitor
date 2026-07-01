// main.jsx — the entry point for the React app.
// This file's only job is to take our top-level <App /> component and
// "mount" it into the <div id="root"> element in index.html.

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./styles.css";

// Find the root div and render the App into it.
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
