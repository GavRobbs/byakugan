import { createRoot } from 'react-dom/client'
import { HashRouter as Router } from 'react-router';
import './index.css'
import App from './components/App.jsx';
import { AppProvider } from './components/AppContext.jsx';

createRoot(document.getElementById('root')).render(
  <Router>
    <AppProvider>
      <App />
    </AppProvider>    
  </Router>,
)
