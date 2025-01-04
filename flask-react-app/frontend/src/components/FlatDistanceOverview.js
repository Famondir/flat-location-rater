import React, { useEffect, useState, useRef } from 'react';
import { Button, Card, Row, Col, CardHeader, CardText } from 'react-bootstrap';
import DataTable from 'react-data-table-component';
import L from 'leaflet';
import { MapContainer, TileLayer, Marker, Popup, Pane, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import hash from 'object-hash';
import FlatDetailModal from './FlatDetailModal';
import { formatSeconds } from './FormatSeconds';

L.Icon.Default.imagePath='img/'

const FlatDistanceOverview = ({ mapData, geoData, opnvData, aggTravelTimeData }) => {
    const [showModal, setShowModal] = useState(false);
    const [selectedFlatData, setSelectedFlatData] = useState(null);
    const [selectedFlat, setSelectedFlat] = useState(null);
    const [hoveredFlat, setHoveredFlat] = useState(null);
    const markersRef = useRef({});

    const customStyles = {
        rows: {
            style: {
                cursor: 'pointer',
            },
            highlightOnHoverStyle: {
                backgroundColor: 'rgba(0, 0, 0, 0.1)',
            }
        },
        headCells: {
            style: {
                fontWeight: 'bold',
            },
        },
    };

    const handleMarkerClick = (flatName) => {
        setSelectedFlat(flatName);
    };

    const handlePopupClose = () => {
        setSelectedFlat(null);
    };

    const handleRowMouseEnter = (row) => {
        if (row && markersRef.current[row.flat]) {
            markersRef.current[row.flat].openPopup();
            setHoveredFlat(row.flat);
        }
    };

    const handleRowMouseLeave = (row) => {
        if (row && markersRef.current[row.flat]) {
            markersRef.current[row.flat].closePopup();
            setHoveredFlat(null);
        }
    };

    const handleRowClick = row => {
        setSelectedFlatData({
            name: row.flat,
            ...mapData.flat_positions[row.flat]
        });
        setShowModal(true);
    };

    const columns = [{
        name: 'Flat',
        selector: row => row.flat,
        sortable: true
    },
    {
        name: 'Median',
        selector: row => row.median,
        sortable: true,
        format: row => formatSeconds(row.median)
    },
    {
        name: 'Min',
        selector: row => row.min,
        sortable: true,
        format: row => formatSeconds(row.min)
    },
    {
        name: 'Std Dev',
        selector: row => row.std,
        sortable: true,
        format: row => formatSeconds(row.std)
    }];

    return (
        <div>
            <Row>
                {aggTravelTimeData && (<Col xxl={6}>
                    <Card className='mb-3'>
                        <CardHeader>
                            <Card.Title>Weekly Travel Time</Card.Title>
                        </CardHeader>
                        <Card.Body>
                        <DataTable
                            columns={columns}
                            data={aggTravelTimeData}
                            pagination
                            paginationPerPage={5}
                            paginationRowsPerPageOptions={[5,10]}
                            highlightOnHover
                            responsive
                            customStyles={customStyles}
                            onRowMouseEnter={handleRowMouseEnter}
                            onRowMouseLeave={handleRowMouseLeave}
                            onRowClicked={handleRowClick}
                            conditionalRowStyles={[
                                {
                                    when: row => row.flat === selectedFlat,
                                    style: {
                                        backgroundColor: 'rgba(26, 132, 214, 0.2)',
                                    },
                                },
                            ]}
                        />
                        <CardText className='text-muted'>If the location of the flat is known without uncertainty (street name and number are available) there is no uncertainty about the weekly travel time. Thus the standard deviation of the median is neither available nor needed. One could think of it to be equal zero.</CardText>
                        </Card.Body>
                    </Card>
                </Col>)}
                <Col xxl={6}>
                    <Card className='mb-3'>
                        <CardHeader>
                            <Card.Title>Flat Distance Overview</Card.Title>
                        </CardHeader>
                        <Card.Body>
                            <div style={{ height: '600px' }}>
                                <MapContainer 
                                    center={mapData.center} 
                                    zoom={mapData.zoom} 
                                    scrollWheelZoom={false}>
                                    <TileLayer
                                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                    // url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                                    url="http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png" 
                                    />
                                    {mapData.poi_positions && Object.entries(mapData.poi_positions).length > 0 && (
                                        Object.entries(mapData.poi_positions).map(([name, coords]) => (
                                            <Marker 
                                                key={`poi-${name}`} 
                                                position={[coords.latitude, coords.longitude]}
                                            >
                                                <Popup>{name}</Popup>
                                            </Marker>
                                        )))}
                                    <Pane name="flatMarkerPane"></Pane>
                                    <Pane name="flatAreaMarkerPane"></Pane>
                                    {mapData.flat_positions && Object.entries(mapData.flat_positions).length > 0 && (
                                        Object.entries(mapData.flat_positions).map(([name, param]) => (
                                            param.is_point && (
                                                <Marker
                                                    key={name} 
                                                    position={[param.latitude, param.longitude]}
                                                    pane='flatMarkerPane'
                                                    ref={(ref) => {
                                                        if (ref) markersRef.current[name] = ref;
                                                    }}
                                                    eventHandlers={{
                                                        click: () => handleMarkerClick(name),
                                                        popupclose: handlePopupClose
                                                    }}
                                                >
                                                    <Popup>{name}</Popup>
                                                </Marker>
                                    ))))}                          
                                    {mapData.flat_positions && Object.entries(mapData.flat_positions).length > 0 && (
                                        Object.entries(mapData.flat_positions).map(([name, param]) => (
                                            !param.is_point && (
                                                <Marker 
                                                    key={name}
                                                    position={[param.latitude, param.longitude]}
                                                    pane='flatAreaMarkerPane'
                                                    ref={(ref) => {
                                                        if (ref) markersRef.current[name] = ref;
                                                    }}
                                                    eventHandlers={{
                                                        click: () => handleMarkerClick(name),
                                                        popupclose: handlePopupClose
                                                    }}
                                                >
                                                    <Popup>{name}</Popup>
                                                </Marker>
                                    ))))}
                                    {<GeoJSON 
                                        data={opnvData} 
                                        key={hash(opnvData)} 
                                        style={{
                                            color: 'lightsalmon',
                                            fillColor: "lightsalmon",
                                            fillOpacity: 1,
                                            weight: 2
                                        }}
                                        />}
                                    {<GeoJSON 
                                        data={geoData} 
                                        key={hash(geoData)} 
                                        style={{fillColor: "lightgreen"}} 
                                        pathOptions={{color:'green'}}
                                        />}
                                </MapContainer>
                            </div>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
            {showModal && (<FlatDetailModal
                show={showModal}
                onHide={() => setShowModal(false)}
                flatData={selectedFlatData}
            />)}
        </div>
        
    );
};

export default FlatDistanceOverview;