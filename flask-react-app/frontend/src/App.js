import {socket} from "./components/socket";
import React, { useState, useEffect } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Navbar, Nav, Row, Col, Button } from 'react-bootstrap';
import FlatDistanceOverview from './components/FlatDistanceOverview';
import Sidebar from './components/Sidebar';
import { Map } from 'react-bootstrap-icons';
import About from './components/About';
import SetFlatLocations from "./components/SetFlatLocations";
import './styles/App.css';
import { List } from 'react-bootstrap-icons';

function App() {
    const [view, setView] = useState('flat-distance');
    const [mapData, setMapData] = useState({
        center: [52.510885, 13.3989367],
        zoom: 11,
        poi_positions: {'Berliner Dom': {latitude: 52.5194, longitude: 13.4023}},
        flat_positions: {'Alexanderplatz': {latitude: 52.5219, longitude: 13.4133}}
    });
    const [geoData, setGeoData] = useState(null);
    const [opnvData, setOpnvData] = useState(null);
    const [aggTravelTimeData, setAggTravelTimeData] = useState(null);
    const [sidebarVisible, setSidebarVisible] = useState(true);
    
    useEffect(() => {
        socket.emit('/api/connect');

        // Initial data fetch
        socket.emit('/api/get-map-data');
        socket.emit('/api/get-geo-data');
        socket.emit('/api/get-opnv-data');
        socket.emit('/api/get-aggregated-travel-time-data');

        socket.on('map_data', (data) => {
            setMapData(data);
        });

        socket.on('geo_data', (data) => {
            setGeoData(data);
        });

        socket.on('opnv_data', (data) => {
            setOpnvData(data);
        });

        socket.on('aggregated_travel_time_data', (data) => {
            console.log(data);
            setAggTravelTimeData(data);
        });

    }, []);

    const renderContent = () => {
        switch (view) {
            case 'about':
                return <About />;
            case 'flat-distance':
                return <FlatDistanceOverview 
                    mapData={mapData} 
                    geoData={geoData} 
                    opnvData= {opnvData}
                    aggTravelTimeData={aggTravelTimeData}  
                />;
            case 'flat-location':
                return <SetFlatLocations />;
        };
    };

    return (
        <>
            <Navbar bg="dark" variant="dark" expand="md">
                <Container>
                    <Navbar.Brand href="#" onClick={() => setView('about')}><Map /></Navbar.Brand>
                    <Navbar.Toggle aria-controls="basic-navbar-nav" />
                    <Navbar.Collapse id="basic-navbar-nav">
                        <Nav className="me-auto">
                            <Nav.Link href="#" onClick={() => setView('flat-distance')}>Flat Distance</Nav.Link>
                            <Nav.Link href="#">Meet Fair</Nav.Link>
                        </Nav>
                    </Navbar.Collapse>
                </Container>
            </Navbar>
            <Container fluid>
                <Button 
                    variant="outline-light" 
                    className={`me-2 sidebar-toggle ${sidebarVisible ? 'show' : 'hide'}`}
                    onClick={() => setSidebarVisible(!sidebarVisible)}
                >
                    <List />
                </Button>
                <Row>
                    <Col xs={sidebarVisible ? 2 : 0} id="sidebar-wrapper"
                        className={`sidebar-nav ${sidebarVisible ? 'show' : 'hide'}`}
                    >
                        <Sidebar  setView={setView} />
                    </Col>
                    <Col xs={sidebarVisible ? 10 : 12} className='mt-2'>
                        {renderContent()}
                    </Col>
                </Row>
            </Container>
        </>
    );
}

export default App;