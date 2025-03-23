import { useContext, useEffect, useState } from "react";
import { AppContext } from "./AppContext";

export default function Settings(){

    const [recordingEnabled, setRecordingEnabled] = useState(true);
    const [processingMethod, setProcessingMethod] = useState(0);

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
        });

        fetch(`/api/processor`, {
            method: "GET",
        })
        .then(response => response.json())
        .then(response => {
            setProcessingMethod(parseInt(response["method"]))
        })
        .catch(err => {
            console.log("Error getting processing method");
            setRecordingEnabled(false);
        });
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
    
    function changeSubtractorMethod(event){

        fetch("/api/processor", {
            method: "POST",
            body: JSON.stringify({method : event.target.value}),
            headers: { "Content-Type" : "application/json"}
        })
            .then((response) => response.json())
            .then((result) => {
                console.log("Background subtractor method changed successfully");
                setProcessingMethod(parseInt(event.target.value));
            })
            .catch((err) => {
                console.log("Error changing background subtractor method");
            });

    }

    return ( 
        <main>
            <h1>Settings</h1>
            <div className="alert-container">
                <section className="settings-section">
                    <h2>Enable or Disable Recording</h2>
                    <div className="settings-recording-button-holder">
                        {renderRecordingButton()}
                    </div>
                </section>
                <section className="settings-section">
                    <h2>Background Subtraction Method</h2>
                    <div className="settings-radio-options">
                        <label>
                            <input
                            type="radio"
                            name="subtractor"
                            value="0"
                            onChange={changeSubtractorMethod}
                            checked={processingMethod === 0}
                            />
                            Custom Moving Median Background Subtractor
                        </label>

                        <label>
                            <input
                            type="radio"
                            name="subtractor"
                            value="1"
                            onChange={changeSubtractorMethod}
                            checked={processingMethod === 1}
                            />
                            OpenCV MOG2 Background Subtractor
                        </label>
                    </div>
                </section>
            </div>
        </main>
        )
}