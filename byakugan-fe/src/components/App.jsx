import { Routes, Route } from 'react-router';
import Home from './Home.jsx';
import Navbar from './Navbar.jsx';
import Alerts from './Alerts.jsx';
import LiveFeed from './LiveFeed.jsx';
import Settings from './Settings.jsx';
import AlertDetails from './AlertDetails.jsx';
import { Toaster } from 'react-hot-toast';

export default function App(){

    function renderCoreApp(){
        return (
            <>
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
             </>
        )
    }   

    return renderCoreApp();
}