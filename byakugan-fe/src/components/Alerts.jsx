import { useEffect, useState } from "react"
import { useNavigate } from "react-router";
import { useContext } from "react";
import { AppContext } from "./AppContext";

export default function Alerts(){

    let [alerts, setAlerts] = useState([]);

    const alerts_url = `/api/alerts`;
    const thumbnail_url = `/api/thumbnails/`;

    const navigate = useNavigate();

    useEffect(() => {

        fetch(alerts_url, {
            "method": "GET",
            headers: { "Content-Type" : "application/json"}
        })
        .then(response => response.json())
        .then((result) => {

            setAlerts(result);
        })
    }, []);


    return ( 
        <main>
            <h1>Alerts</h1>
            <div className="alert-container">
            {
                alerts.map((alert, index) => {

                    const nav_url = "/alerts/" + alert.id;

                    return (
                    <div key={index} className="alert-box" onClick={() => navigate(nav_url)}>
                        <h2>{alert.timestamp}</h2>
                        <div className="alert-box-desc">
                            <img src={thumbnail_url + alert.thumbnail} />
                            <p>{alert.description}</p>
                        </div>
                    </div>);

                })
            }
                <div className="paginator">
                    <button className="btn btn-primary">Previous</button>
                    <span>Page 1</span>
                    <button className="btn btn-primary">Next</button>
                </div>
            </div>
            
        </main>
        )
}