import { useContext, useEffect, useState } from "react";
import { AppContext } from "./AppContext";

export default function Settings(){

    const [recordingEnabled, setRecordingEnabled] = useState(true);

    useEffect(()=> {
        
        fetch(`/api/record_status`, {
            method: "GET",
        })
        .then(response => response.json())
        .then(response => {
            if(response["recording"] == "enabled")
            {
                setRecordingEnabled(true);
            } else{
                setRecordingEnabled(false);
            }
        })
        .catch(err => {
            console.log("Error getting recording status");
            setRecordingEnabled(false);
        })

    }, []);

    function disableRecording()
    {
        fetch("/api/record_status", {
            method: "POST",
            body: JSON.stringify({new_state : "disabled"}),
            headers: { "Content-Type" : "application/json"}
        })
            .then((response) => response.json())
            .then((result) => {
                console.log("Recording disabled");
                setRecordingEnabled(false);
            })
            .catch((err) => {
                console.log("Error disabling recording");
            });

    }

    function enableRecording(){

        fetch("/api/record_status", {
            method: "POST",
            body: JSON.stringify({new_state : "enabled"}),
            headers: { "Content-Type" : "application/json"}
        })
            .then((response) => response.json())
            .then((result) => {
                console.log("Recording enabled");
                setRecordingEnabled(true);
            })
            .catch((err) => {
                console.log("Error enabling recording");
            });

    }

    function renderRecordingButton(){
        if(recordingEnabled == true){
            return <button className="btn btn-cancel" onClick={disableRecording}>Disable Recording</button>;
        } else{
            return <button className="btn btn-primary" onClick={enableRecording}>Enable Recording</button>;
        }
    }

    return ( 
        <main>
            <h1>Settings</h1>
            {renderRecordingButton()}
        </main>
        )
}