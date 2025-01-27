import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";
import {toast} from "react-hot-toast";


export default function AlertDetails(){

    const {id} = useParams();
    const navigator = useNavigate();

    const details_url = "http://192.168.0.185:5000/alerts/" + id;
    const video_url = "http://192.168.0.185:5000/recordings/";

    const [alertData, setAlertData] = useState({
        id: "",
        timestamp: "",
        description: "",
        video: ""
    });

    useEffect(() => {
        fetch(details_url, {
            method: "GET",
            headers: { "Content-Type" : "application/json"}
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            setAlertData(data);
        })
    }, []);

    const generateDownload = () => {
        const link = document.createElement("a");
        link.href = video_url + alertData.video + "?download=yes"; // URL of the file
        link.download = alertData.video;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const deleteAlert = () => {

        fetch(details_url, {
            method: "DELETE",
        })
        .then(response => response.json())
        .then(data => {

            toast.success("Alert deleted!", {duration: 4000});
            navigator("/alerts");
        })

    }

    return ( 
        <main>
            <h1>Alert Details</h1>
            <div className="alert-details-holder">
            {
                alertData.video ? ( <video controls>
                    <source src={video_url + alertData.video} type="video/mp4"/>
                </video>) : <p>Loading video...</p>
            }
                <div className="alert-video-details">
                    <h3>{alertData.timestamp}</h3>
                    <h4>Description</h4>
                    <p>{alertData.description}</p>
                    <div className="alert-video-buttons">
                        <button className="btn btn-primary" onClick={generateDownload}>DOWNLOAD VIDEO</button>
                        <button className="btn btn-cancel" onClick={deleteAlert}>DELETE VIDEO</button>
                    </div>  
                </div>
            </div>
           
        </main>
        )

}