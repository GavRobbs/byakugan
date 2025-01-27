import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router';
import './index.css'
import Home from './components/Home.jsx';
import Navbar from './components/Navbar.jsx';
import Alerts from './components/Alerts.jsx';
import LiveFeed from './components/LiveFeed.jsx';
import Settings from './components/Settings.jsx';
import AlertDetails from './components/AlertDetails.jsx';
import { Toaster } from 'react-hot-toast';

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <Navbar />
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/alerts" element={<Alerts />} />
      <Route path="/alerts/:id" element={<AlertDetails />} />
      <Route path="/livefeed" element={<LiveFeed />} />
      <Route path="/settings" element={<Settings />} />
    </Routes>
    <Toaster position="bottom-right" 
            reverseOrder={false}
            toastOptions={{
              style: {
                background: '#E6F7EC',
                border: '2px solid #80AB8E'
              }
            }}
             />
  </BrowserRouter>,
)
