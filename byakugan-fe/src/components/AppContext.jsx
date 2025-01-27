import { createContext, useState } from "react"

export const AppContext = createContext();

export const AppProvider = ({children}) => {

    const [settingsData, setSettingsData] = useState({
        'server_ip' : localStorage.getItem("byakugan_server_ip") || "127.0.0.1:5000"
    });

    function updateServerIP(ip_addr){
        localStorage.setItem("byakugan_server_ip", ip_addr);
        setSettingsData(prev => {
            return {...prev, 'server_ip' : ip_addr}
        });
    }

    return (
        <AppContext.Provider value={{settingsData, updateServerIP}}>
            {children}
        </AppContext.Provider>
    )
};