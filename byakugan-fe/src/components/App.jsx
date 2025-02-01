import { Routes, Route } from 'react-router';
import Home from './Home.jsx';
import Navbar from './Navbar.jsx';
import Alerts from './Alerts.jsx';
import LiveFeed from './LiveFeed.jsx';
import Settings from './Settings.jsx';
import AlertDetails from './AlertDetails.jsx';
import { Toaster } from 'react-hot-toast';
import { AppContext, AppProvider } from './AppContext.jsx';
import { useContext, useEffect, useState } from 'react';
import QRCodeImage from "../assets/qr.png"

export default function App(){

    const [isSetup, setIsSetup] = useState([false, false]);
    const {settingsData, updateServerIP} = useContext(AppContext);

    useEffect(() => {

        fetch(`http://${settingsData.server_ip}/api/setup`, {
            method: "GET",
            headers: { "Content-Type" : "application/json"}
        })
        .then(response => response.text())
        .then(data => {

            console.log(data);

            if(data == "COMPLETE"){
                console.log("Setup complete");
                setIsSetup([true, true]);
            } else{
                console.log("Setup incomplete");
                setIsSetup([false, false]);
            }

        })
        .catch(err => {
            console.log("Failed to connect");
            setIsSetup([false, false]);
        })

    }, []);

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

    function testConnection(e){

        e.preventDefault();
        const form_data = new FormData(e.target);


        //Calls a function at the backend that returns 200 if the connection is successful

        const ip_addr = form_data.get("ipaddr");

        console.log("TC called");

        fetch(`http://${ip_addr}/api/setup/check_connection`, {
            method: "GET",
        })
        .then(response => {

            if(response.ok){
                updateServerIP(ip_addr);
                setIsSetup([true, false]);
            } else{
                console.log("NOT OK");
            }

        })
        .catch(err => {

            console.log("Couldn't find server");
        })

    }

    function testChatID(e){

        //Links the chat ID
        e.preventDefault();
        const form_data = new FormData(e.target);
        const chat_id = form_data.get("chatid");
        const ip_addr = settingsData.server_ip;

        const body = {"chat_id" : chat_id};

        fetch(`http://${ip_addr}/api/setup/link_bot`, {
            method: "POST",
            headers: { "Content-Type" : "application/json"},
            body: JSON.stringify(body)
        })
        .then(response => {

            console.log("App linked to bot");
            setIsSetup([true, true]);

        })
        .catch(err => {
            console.log("Error linking app to bot");
        })

    }

    function renderSetupForm(){

        if(isSetup[0] == false){
            return (
                <>
                    <main>
                        <h1>Setup</h1>
                        <h2>Step 1</h2>
                        <p style={{maxWidth: "800px"}}>First, set up the IP address of the backend server. This is critical for Byakugan to function properly. If you're deploying the backend and the frontend from the same computer, leave the default value as is. Otherwise, enter the IP values as an IPv4 address in the following format: X.X.X.X:PORT. </p>
                        <form onSubmit={testConnection} method="POST">
                            <input type="text" defaultValue={"127.0.0.1:5000"} id="ipaddr" name="ipaddr" />
                            <input type="submit" value={"Submit"} />
                        </form>
                    </main>
                </>)
        } else{
            return <>
                <main>
                    <h1>Setup</h1>
                    <h2>Step 2</h2>
                    <p style={{maxWidth: "800px"}}>Now let's setup the telegram bot so you can receive notifications. Scan the QR code below or click the link and type /start when the bot opens to get your chat ID. Enter the chat ID in the box below: </p>
                    <a href="https://t.me/byakugan_avssbot" target="_blank">
                        <img src={QRCodeImage} />
                    </a>
                    <form onSubmit={testChatID} method="POST">
                        <input type="text" id="chatid" name="chatid" />
                        <input type="submit" value={"Submit"} />
                    </form>
                </main>
            </>

        }
        
    }

    return ( (isSetup[0] == true && isSetup[1] == true) ? renderCoreApp() : renderSetupForm());
}