import {socket} from "./socket";
import React, { useEffect, useState } from 'react';
import { Modal, Row, Col, Card, CardHeader } from 'react-bootstrap';
import { MapContainer, TileLayer, Marker, Popup, GeoJSON } from 'react-leaflet';
import L from 'leaflet';
import hash from 'object-hash';
import DataTable from 'react-data-table-component';
import { formatSeconds } from './FormatSeconds';
import { interpolateRdYlGn } from 'd3-scale-chromatic';
// import 'leaflet/dist/leaflet.css';

const onEachFeature = (feature, layer) => {
    if (feature.properties && feature.properties.scale) {
        const { scale } = feature.properties;
        const color = interpolateRdYlGn(scale);

        layer.setStyle({ 
            fillColor: color,
            fillOpacity: 0.5
        });

    }

    if (feature.properties.travelTime) {
        layer.bindPopup(`Weekly Travel Time: ${formatSeconds(feature.properties.travelTime)}`);
    }
};

const FlatDetailModal = ({ show, onHide, flatData }) => {
    const [travelTimeData, setTravelTimeData] = useState(null);
    const [hexGeoData, setHexGeoData] = useState(null);
    const defaultCenter = flatData ? [flatData?.latitude, flatData?.longitude] : [52.5200, 13.4050]; // Berlin center
    const defaultZoom = 15;

    useEffect(() => {
        

        socket.emit('/api/get-hex-geo-data', {flat: flatData?.name});

        socket.on('hex_geo_data', (data) => {
                    setHexGeoData(data);
                });
     }, []);

    const columns = [
        {
            name: 'Route',
            selector: row => row.route,
            sortable: true
        },
        {
            name: 'Travel Time',
            selector: row => row.travelTime,
            sortable: true
        }
    ];

    const getBounds = () => {
        // console.log('hexGeoData:', hexGeoData);
        if (!hexGeoData || !hexGeoData.features || hexGeoData.features.length === 0) {
            return null;
        }
        try {
            const bounds = L.latLngBounds([]);
            hexGeoData.features.forEach(feature => {
                const coordinates = feature.geometry.coordinates[0];
                coordinates.forEach(coord => {
                    bounds.extend([coord[1], coord[0]]);
                });
            });
            // console.log('Calculated bounds:', bounds);
            return bounds;
        } catch (error) {
            console.error('Error calculating bounds:', error);
            return null;
        }
    };

    return (
        <Modal show={show} onHide={onHide} size="xl" centered className='almost-fullscreen-modal'>
            <Modal.Header closeButton>
                <Modal.Title>Detailed View: {flatData?.name}</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <Row>
                    <Col xl={6}>
                        <Card className="mb-3">
                            <CardHeader><Card.Title>Travel Time</Card.Title></CardHeader>
                            <Card.Body>
                                 {travelTimeData && (<DataTable
                                    columns={columns}
                                    data={travelTimeData}
                                    pagination
                                    highlightOnHover
                                    responsive
                                />)}
                            </Card.Body>
                        </Card>
                    </Col>
                    <Col xl={6}>
                        <Card>
                            <CardHeader><Card.Title>Location</Card.Title></CardHeader>
                            <Card.Body>
                                <div style={{ height: '400px' }}>
                                    <MapContainer
                                        center={!getBounds() ? defaultCenter : undefined}
                                        zoom={!getBounds() ? defaultZoom : undefined}
                                        bounds={getBounds()}
                                        boundsOptions={hexGeoData && hexGeoData.features.length === 0 ? { padding: [500, 500] } : { padding: [50, 50] }}
                                        key={hash(hexGeoData)} 
                                        style={{ height: '100%', width: '100%' }}
                                    >
                                        <TileLayer
                                            url="http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
                                        />
                                        <Marker position={[flatData?.latitude, flatData?.longitude]}>
                                            <Popup>{flatData?.name}</Popup>
                                        </Marker>
                                        {<GeoJSON 
                                            data={hexGeoData} 
                                            key={hash(hexGeoData)}
                                            pathOptions={{color:'green'}}
                                            onEachFeature={onEachFeature}
                                            />}
                                    </MapContainer>
                                </div>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            </Modal.Body>
        </Modal>
    );
};

export default FlatDetailModal;