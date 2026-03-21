import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { PortfolioProvider } from './context/PortfolioContext.jsx'
import { AdminProvider } from './context/AdminContext.jsx'
import { BrowserRouter } from 'react-router-dom'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AdminProvider>
        <PortfolioProvider>
          <App />
        </PortfolioProvider>
      </AdminProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
