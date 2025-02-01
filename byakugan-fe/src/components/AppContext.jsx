import { createContext, useState, useEffect } from "react"
import QRCodeImage from "../assets/qr.png"

export const AppContext = createContext();

export const AppProvider = ({children}) => {

    const [isSetup, setSetup] = useState(null);
    const [isLoading, setLoading] = useState(true);

    useEffect(() => {

        fetch(`/api/setup`, {
            method: "GET",
            headers: { "Content-Type" : "application/json"}
        })
        .then(response => response.text())
        .then(data => {

            console.log(data);

            if(data == "COMPLETE"){
                setSetup(true);
            } else{
                setSetup(false);
            }
        })
        .catch(err => {
            console.log("Failed to connect");
            setSetup(false);
        })
        .finally(() => {
            setLoading(false);
        })

    }, []);

    function testChatID(e){

        //Links the chat ID
        e.preventDefault();
        const form_data = new FormData(e.target);
        const chat_id = form_data.get("chatid");

        const body = {"chat_id" : chat_id};

        fetch(`/api/setup/link_bot`, {
            method: "POST",
            headers: { "Content-Type" : "application/json"},
            body: JSON.stringify(body)
        })
        .then(response => {

            console.log("App linked to bot");
            setSetup(true);

        })
        .catch(err => {
            console.log("Error linking app to bot");
            setSetup(false);
        })

    }

    function renderSetupForm(){

        
        return <>
            <main>
                <h1>Setup</h1>
                <p style={{maxWidth: "800px"}}>Let's setup the telegram bot so you can receive notifications. Scan the QR code below or click the link and type /start when the bot opens to get your chat ID. Enter the chat ID in the box below: </p>
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

    if(isLoading){

        return <>
            <main>
                <h1>Loading...</h1>
            </main>
        </>

    }

    return isSetup ? 
        (<AppContext.Provider value={{isSetup}}>
            {children}
        </AppContext.Provider>) : renderSetupForm();
};