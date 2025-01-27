import { useEffect, useState, useRef, useContext } from "react"
import { AppContext } from "./AppContext";

export default function LiveFeed(){

    const {settingsData} = useContext(AppContext);

    //The first variable is the actual value of recording or not, the second is if it should be sent to the server
    const [isRecording, setIsRecording] = useState([false, false]);
    const record_url = `http://${settingsData.server_ip}/record`;


    //The timer is used to automatically activate/deactivate the button

    const recording_timer = useRef(null);

    function startRecordingTimer(){
        if(!recording_timer.current){
            recording_timer.current = setTimeout(() => {
                setIsRecording([false, true]);
            }, 10000);
        }
    }

    function cancelRecordingTimer(){
        if(recording_timer.current){
            clearTimeout(recording_timer.current);
            setIsRecording([false, false]);
        }
    }

    useEffect(() => {

        if(isRecording[1] == false){
            //Leave early because we didn't want to send this to the server
            return;
        }

        if(isRecording[0]){
            //Send the request to start the recording
            fetch(record_url, {
                method: "POST",
                body: JSON.stringify({new_state : "on"}),
                headers: { "Content-Type" : "application/json"}
            })
                .then((response) => response.json())
                .then((result) => {

                    console.log(result);
                    startRecordingTimer();

                })
                .catch((err) => {
                    console.log("Error starting recording");
                    setIsRecording([false, false]);
                });
        } else{
            //Send the request to stop the recording
            cancelRecordingTimer();
            fetch(record_url, {
                method: "POST",
                body: JSON.stringify({new_state : "off"}),
                headers: { "Content-Type" : "application/json"}
            })
                .then((response) => response.json())
                .then((result) => {

                    console.log(result);

                })
                .catch((err) => {
                    console.log("Error starting recording");
                    setIsRecording([false, false]);
                });
        }

    }, [isRecording]);

    function renderButton(){

        if(!isRecording[0]){

            return <button className="btn btn-primary" 
        style={{maxWidth:'350px'}} 
        onClick={() => setIsRecording((prev) => [!prev[0], true])}>
            ⏺ Start Recording
        </button>;

        } else{

            return <button className="btn btn-cancel" 
        style={{maxWidth:'350px'}} 
        onClick={() => setIsRecording((prev) => [!prev[0], true])}>
            ⏹ Stop Recording
        </button>;

        }

    }

    return ( 
        <main>
            <h1>Live Feed</h1>
            <img src={`http://${settingsData.server_ip}/`} className="mjpg-feed"/>
            {
                renderButton()
            }
            
        </main>
        )
}