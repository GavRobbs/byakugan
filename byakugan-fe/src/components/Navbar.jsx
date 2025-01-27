import { NavLink } from "react-router";

export default function Navbar(){

    return (
    <nav className="navbar">
        <h1>Byakugan</h1>
        <ul className="navbar-list">
            <NavLink to="/" className={({isActive}) => isActive ? "navbar-item-active" : "navbar-item"}>Home</NavLink>
            <NavLink to="/alerts" className={({isActive}) => isActive ? "navbar-item-active" : "navbar-item"}>Alerts</NavLink>
            <NavLink to="/livefeed" className={({isActive}) => isActive ? "navbar-item-active" : "navbar-item"}>Live Feed</NavLink>
            <NavLink to="/settings" className={({isActive}) => isActive ? "navbar-item-active" : "navbar-item"}>Settings</NavLink>
        </ul>
    </nav>
    )
}