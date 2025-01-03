import React, { useEffect, useState, useRef } from 'react';
import { Button, Card, Row, Col, CardHeader } from 'react-bootstrap';
import DataTable from 'react-data-table-component';
import L from 'leaflet';
import { MapContainer, TileLayer, Marker, Popup, Pane, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import hash from 'object-hash';

L.Icon.Default.imagePath='img/'

const onEachFeature = (feature, layer) => {
    if (feature.properties && feature.properties.opacity) {
        const { opacity } = feature.properties;
        layer.setStyle({ fillOpacity: opacity });
    }
};

const FlatDistanceOverview = ({ mapData, geoData, opnvData, travelTimeData }) => {
    // console.log(travelTimeData)

    const customStyles = {
        headCells: {
            style: {
                fontWeight: 'bold',
            },
        },
    };

    const columns = [{
        name: 'Flat',
        selector: row => row.flat,
        sortable: true
    },
    {
        name: 'Travel Time Sum',
        selector: row => row.sum,
        sortable: true,
        format: row => formatSeconds(row.sum)
    },
    {
        name: 'Median Travel Time',
        selector: row => row.median,
        sortable: true,
        format: row => formatSeconds(row.median)
    },
    {
        name: 'Std Dev',
        selector: row => row.std,
        sortable: true,
        format: row => formatSeconds(row.std)
    }];

    const formatSeconds = (seconds) => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}min`;
    };

    return (
        <div>
            <Row>
                <Col xl={6}>
                    <Card>
                        <CardHeader>
                            <Card.Title>Flat Distance Overview</Card.Title>
                        </CardHeader>
                        <Card.Body>
                            <div style={{ height: '600px' }}>
                                <MapContainer center={mapData.center} zoom={mapData.zoom} scrollWheelZoom={false}>
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
                                                    key={`flat-${name}`} 
                                                    position={[param.latitude, param.longitude]}
                                                    pane='flatMarkerPane'
                                                >
                                                    <Popup>{name}</Popup>
                                                </Marker>
                                    ))))}                          
                                    {mapData.flat_positions && Object.entries(mapData.flat_positions).length > 0 && (
                                        Object.entries(mapData.flat_positions).map(([name, param]) => (
                                            !param.is_point && (
                                                <Marker
                                                    key={`flat-${name}`} 
                                                    position={[param.latitude, param.longitude]}
                                                    pane='flatAreaMarkerPane'
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
                                        style={{fillColor: "red"}} 
                                        onEachFeature={onEachFeature} 
                                        />}
                                </MapContainer>
                            </div>
                        </Card.Body>
                    </Card>
                </Col>
                {travelTimeData && (<Col xl={6}>
                    <Card>
                        <CardHeader>
                            <Card.Title>Flat Distance Overview</Card.Title>
                        </CardHeader>
                        <Card.Body>
                        <DataTable
                            columns={columns}
                            data={travelTimeData}
                            pagination
                            highlightOnHover
                            responsive
                            customStyles={customStyles}
                        />
                        </Card.Body>
                    </Card>
                </Col>)}
            </Row>
        </div>
        
    );
};

export default FlatDistanceOverview;