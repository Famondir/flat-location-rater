import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Navbar, Nav, Row, Col } from 'react-bootstrap';
import FlatDistanceOverview from './components/FlatDistanceOverview';
import Sidebar from './components/Sidebar';
import { Map } from 'react-bootstrap-icons';
import About from './components/About';
import './styles/App.css';

const socket = io(process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000'); // Backend URL

function App() {
    const [view, setView] = useState('flat-distance');
    const [mapData, setMapData] = useState({
        center: [52.510885, 13.3989367],
        zoom: 11,
        poi_positions: {'Berliner Dom': {latitude: 52.5194, longitude: 13.4023}},
        flat_positions: {'Alexanderplatz': {latitude: 52.5219, longitude: 13.4133}}
    });
    const [geoData, setGeoData] = useState(null);

    useEffect(() => {
        socket.emit('/api/connect');

        // Initial data fetch
        socket.emit('/api/get-map-data');
        socket.emit('/api/get-geo-data');

        socket.on('map_data', (data) => {
            setMapData(data);
            console.log(data);
        });

        socket.on('geo_data', (data) => {
            setGeoData(data);
        });

    }, []);

    const renderContent = () => {
        switch (view) {
            case 'about':
                return <About />;
            case 'flat-distance':
                return <FlatDistanceOverview mapData={mapData} geoData={geoData} />;
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
                <Row>
                    <Col xs={2} id="sidebar-wrapper">
                        <Sidebar  setView={setView} />
                    </Col>
                    <Col xs={10} className='mt-2'>
                        {renderContent()}
                    </Col>
                </Row>
            </Container>
        </>
    );
}

export default App;