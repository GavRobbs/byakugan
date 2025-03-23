import { useEffect, useState } from "react"

export default function Home(){

    const [platformInfo, setPlatformInfo] = useState(null);

    useEffect(()=>{

        fetch(`/api/platform`, {
            method: "GET",
        })
        .then(response => response.json())
        .then(response => {
            console.log(response);
            setPlatformInfo(response);
        })
        .catch(err => {
            console.log("Error getting platform data");
            setPlatformInfo(null);
        });

    }, []);

    function renderPlatformString(){
        return (
        <>
            <h2>Container Information</h2>
            <p>System: {platformInfo.system}</p>
            <p>Release: {platformInfo.release}</p>
            <p>Version: {platformInfo.version}</p>
            <p>Machine: {platformInfo.machine}</p>
        </>
        )

    }

    return ( 
    <main>
        <h1>Home</h1>
        <div className="alert-container">
            {platformInfo === null ? <p>No platform info available</p> : renderPlatformString()}
        </div>
        
    </main>
    )
}