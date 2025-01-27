import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router';
import './index.css'
import App from './components/App.jsx';
import { AppProvider } from './components/AppContext.jsx';

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <AppProvider>
      <App />
    </AppProvider>    
  </BrowserRouter>,
)
