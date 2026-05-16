import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
// import "aws-amplify/auth/enable-oauth-listener";
// import React from "react";
// import ReactDOM from "react-dom/client";
// import App from "./App";

// import { Amplify } from "aws-amplify";
// import awsConfig from "./aws-config";

// import "@aws-amplify/ui-react/styles.css";

// Amplify.configure(awsConfig);

// ReactDOM.createRoot(document.getElementById("root")).render(
//   <React.StrictMode>
//     <App />
//   </React.StrictMode>
// );