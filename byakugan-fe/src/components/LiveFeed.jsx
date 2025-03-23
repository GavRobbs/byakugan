import { useEffect, useState, useRef, useContext } from "react"
import { AppContext } from "./AppContext";
import NoFeedImage from "../assets/nofeed.jpg";

export default function LiveFeed(){

    const {settingsData} = useContext(AppContext);

    //The first variable is the actual value of recording or not, the second is if it should be sent to the server
    const [isRecording, setIsRecording] = useState([false, false]);
    const [isRecordingAllowed, setIsRecordingAllowed] = useState(true);
    const record_url = `/api/record`;

    //The timer is used to automatically activate/deactivate the button

    const recording_timer = useRef(null);

    //We make an API call here to see if the user has enabled or disabled recording
    //so we can know to put the placeholder there if not
    useEffect(() => {

        fetch(`/api/record_status`, {
            method: "GET",
        })
        .then(response => response.json())
        .then(response => {
            if(response["recording"] == "enabled")
            {
                setIsRecordingAllowed(true);
            } else{
                setIsRecordingAllowed(false);
            }
        })
        .catch(err => {
            console.log("Error getting recording status");
            setIsRecordingAllowed(false);
        })

    }, []);    

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

                })
                .catch((err) => {
                    console.log("Error starting recording");
                    setIsRecording([false, false]);
                });
        }

    }, [isRecording]);

    function renderButton(){

        if(!isRecordingAllowed){
            return;
        }

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

    function renderFeedOrPlaceHolder(){
        if(isRecordingAllowed){
            return <img src={`/api/live`} className="mjpg-feed"/>;
        } else{
            return <img src={NoFeedImage} className="mjpg-feed" />;
        }
    }

    return ( 
        <main>
            <h1>Live Feed</h1>
            {
                renderFeedOrPlaceHolder()
            }
            {
                renderButton()
            }       
        </main>
        )
}