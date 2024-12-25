import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
// import 'bootstrap/dist/css/bootstrap.min.css';
import { Container } from 'react-bootstrap';
import ExampleComponent from './components/ExampleComponent';

const socket = io(process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000'); // Backend URL

function App() {
    return (
        <Container>
            <h1>Welcome to the Flask-React App</h1>
            <ExampleComponent />
        </Container>
    );
}

export default App;