import React from "react";
import { Nav } from "react-bootstrap";
import '../styles/Sidebar.css'

const Sidebar = ({ setView }) => {   

    return (
        <>
            <Nav className="d-block bg-light sidebar"
            activeKey="/home"
            onSelect={selectedKey => setView(selectedKey)}
            >
                <div className="sidebar-sticky"></div>
            <Nav.Item>
                <Nav.Link eventKey="flat-distance">Overview</Nav.Link>
            </Nav.Item>
            <Nav.Item>
                <Nav.Link eventKey="poi-location">Set POI</Nav.Link>
            </Nav.Item>
            <Nav.Item>
                <Nav.Link eventKey="flat-location">Set flat locations</Nav.Link>
            </Nav.Item>
            <Nav.Item>
                <Nav.Link eventKey="disabled" disabled>
                Tutorial
                </Nav.Link>
            </Nav.Item>
            </Nav>
          
        </>
        );
  };

  export default Sidebar