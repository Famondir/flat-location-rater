import React, { useEffect, useState, useRef } from 'react';
import { Button, Card } from 'react-bootstrap';
import L from 'leaflet';
import { MapContainer, TileLayer, Marker, Popup, Pane } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

L.Icon.Default.imagePath='img/'

const FlatDistanceOverview = ({ mapData }) => {
    return (
        <div>
            <Card>
                <Card.Body>
                    <Card.Title>Flat Distance Overview</Card.Title>
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
                            <Pane name="flatMarkerPane">
                            {mapData.flat_positions && Object.entries(mapData.flat_positions).length > 0 && (
                                Object.entries(mapData.flat_positions).map(([name, coords]) => (
                                    <Marker className='red-marker'
                                        key={`flat-${name}`} 
                                        position={[coords.latitude, coords.longitude]}
                                        pane='flatMarkerPane'
                                    >
                                        <Popup>{name}</Popup>
                                    </Marker>
                                )))}
                            </Pane>
                        </MapContainer>
                    </div>
                </Card.Body>
            </Card>
            
        </div>
        
    );
};

export default FlatDistanceOverview;