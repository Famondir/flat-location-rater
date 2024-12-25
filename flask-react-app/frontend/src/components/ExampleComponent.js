import React, { useEffect, useState, useRef } from 'react';
import { Button } from 'react-bootstrap';

const ExampleComponent = () => {
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

export default ExampleComponent;