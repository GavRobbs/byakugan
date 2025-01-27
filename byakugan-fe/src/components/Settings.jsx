import { useContext } from "react";
import { AppContext } from "./AppContext";

export default function Settings(){
 
    const {settingsData, updateServerIP} = useContext(AppContext);

    function updateIP(e){

        e.preventDefault();
        const fd = new FormData(e.target);
        const s_add = fd.get("server_address");
        updateServerIP(s_add);
    }

    return ( 
        <main>
            <h1>Settings</h1>
            <form onSubmit={updateIP} method="POST">
                <p>
                    <label htmlFor="server_address">Server Address: </label>
                    <input type="text" name="server_address" id="server_address" defaultValue={settingsData.server_ip}/>
                </p>
                <input type="submit" title="Update" />
            </form>
        </main>
        )
}