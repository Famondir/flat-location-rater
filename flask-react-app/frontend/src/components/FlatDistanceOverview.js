import React, { useEffect, useState, useRef } from 'react';
import { Button } from 'react-bootstrap';

const FlatDistanceOverview = () => {
    const mapRef = useRef(null);
    const latitude = 51.505;
    const longitude = -0.09;

    const handleClick = () => {
        console.log('Button clicked!');
    };

    return (
        <div>
            <h1>Example Component</h1>
            <Button variant="primary" onClick={handleClick}>
                Click Me
            </Button>
        </div>
    );
};

export default FlatDistanceOverview;