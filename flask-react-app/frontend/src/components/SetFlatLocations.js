import React, { useState, useEffect } from 'react';
import { Card, CardHeader, Button, Form } from 'react-bootstrap';
import DataTable from 'react-data-table-component';
import { Pencil, Trash, Save, X, Upload, FolderFill } from 'react-bootstrap-icons';
import { socket } from './socket';

const SetFlatLocations = () => {
    const [flats, setFlats] = useState([]);
    const [editableRows, setEditableRows] = useState({});
    const [editData, setEditData] = useState({});
    const [filePath, setFilePath] = useState(() => {
        return localStorage.getItem('fredyDbPath') || '';
    });
    
    const [numFlats, setNumFlats] = useState(() => {
        return parseInt(localStorage.getItem('numFlatsToImport')) || 1;
    });

    useEffect(() => {
        localStorage.setItem('fredyDbPath', filePath);
    }, [filePath]);

    useEffect(() => {
        localStorage.setItem('numFlatsToImport', numFlats);
    }, [numFlats]);

    const handleLoadFlats = () => {
        socket.emit('/api/load-fredy-flats', {
            // filepath: filePath,
            number_of_flats: numFlats
        });
    };

    const handlePathSelect = (event) => {
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                // Get directory path by removing filename from full path
                const path = file.webkitRelativePath || file.name;
                setFilePath(path);
            }
        });
        fileInput.click();
    };

    useEffect(() => {
        socket.emit('/api/get-flat-locations');
        
        socket.on('flat_locations', (data) => {
            // console.log(data)
            setFlats(Object.entries(data).map(([name, details]) => ({
                name,
                street: details.street || '',
                number: details.streetnumber || '',
                postcode: details.plz || '',
                state: details.state || 'Berlin'
            })));
        });

        return () => socket.off('flat_locations');
    }, []);

    const handleEdit = (row) => {
        if (editableRows[row.name]) {
            // Save changes
            socket.emit('/api/update-flat', {
                name: row.name,
                data: editData[row.name]
            });
        }
        setEditableRows(prev => ({
            ...prev,
            [row.name]: !prev[row.name]
        }));
    };

    const handleDelete = (row) => {
        socket.emit('/api/delete-flat', { name: row.name });
    };

    const handleDataChange = (row, field, value) => {
        setEditData(prev => ({
            ...prev,
            [row.name]: {
                ...(prev[row.name] || row),
                [field]: value
            }
        }));
    };

    const columns = [
        {
            name: 'Flat',
            selector: row => row.name,
            sortable: true
        },
        {
            name: 'Street',
            selector: row => row.street,
            sortable: true,
            cell: row => editableRows[row.name] ? (
                <input 
                    type="text" 
                    value={editData[row.name]?.street || row.street}
                    onChange={e => handleDataChange(row, 'street', e.target.value)}
                />
            ) : row.street
        },
        {
            name: 'Number',
            selector: row => row.number,
            sortable: true,
            cell: row => editableRows[row.name] ? (
                <input 
                    type="text" 
                    value={editData[row.name]?.number || row.number}
                    onChange={e => handleDataChange(row, 'number', e.target.value)}
                />
            ) : row.number
        },
        {
            name: 'Postcode',
            selector: row => row.postcode,
            sortable: true,
            cell: row => editableRows[row.name] ? (
                <input 
                    type="text" 
                    value={editData[row.name]?.postcode || row.postcode}
                    onChange={e => handleDataChange(row, 'postcode', e.target.value)}
                />
            ) : row.postcode
        },
        {
            name: 'State',
            selector: row => row.state,
            sortable: true,
            cell: row => editableRows[row.name] ? (
                <input 
                    type="text" 
                    value={editData[row.name]?.state || row.state}
                    onChange={e => handleDataChange(row, 'state', e.target.value)}
                />
            ) : row.state
        },
        {
            name: 'Actions',
            cell: row => (
                <div>
                    <Button 
                        variant={editableRows[row.name] ? "success" : "primary"}
                        size="sm"
                        className="me-2 disabled"
                        onClick={() => handleEdit(row)}
                    >
                        {editableRows[row.name] ? <Save /> : <Pencil />}
                    </Button>
                    <Button 
                        variant="danger"
                        size="sm"
                        onClick={() => handleDelete(row)}
                    >
                        <Trash />
                    </Button>
                </div>
            )
        }
    ];

    return (
        <div>
        <Card className="mb-3">
            <CardHeader>
                <Card.Title>Flat Locations</Card.Title>
            </CardHeader>
            <Card.Body>
                <DataTable
                    columns={columns}
                    data={flats}
                    pagination
                    highlightOnHover
                    responsive
                />
            </Card.Body>
        </Card>
        <Card>
            <Card.Header>
                <Card.Title>Import Flats</Card.Title>
            </Card.Header>
            <Card.Body>
            <Form.Group controlId="formFile" className="mb-3">
                <Form.Label>Select file path to fredy database:</Form.Label>
                <div className="d-flex align-items-stretch w-100">
                    <Form.Control
                        type="text"
                        value={filePath}
                        onChange={(e) => setFilePath(e.target.value)}
                        placeholder="Enter file path"
                        className="flex-grow-1"
                        style={{ borderTopRightRadius: 0, borderBottomRightRadius: 0 }}
                    />
                    <Button 
                        variant="outline-primary"
                        onClick={handlePathSelect}
                        className="d-flex align-items-center"
                        style={{ 
                            borderTopLeftRadius: 0, 
                            borderBottomLeftRadius: 0,
                            whiteSpace: 'nowrap'
                        }}
                    >
                        <FolderFill className="me-1" />
                        Browse
                    </Button>
                </div>
                <div className="d-flex align-items-center gap-2 mt-2">
                    <Form.Control
                        type="number"
                        value={numFlats}
                        onChange={(e) => setNumFlats(parseInt(e.target.value))}
                        min={1}
                        max={100}
                        style={{ maxWidth: '100px' }}
                    />
                    <Button 
                        variant="primary"
                        onClick={handleLoadFlats}
                        className="d-flex align-items-center"
                        disabled={!filePath}
                    >
                        <Upload className="me-1" />
                        Load Flats
                    </Button>
                </div>
            </Form.Group>
            </Card.Body>
            <Card.Footer>
                Note: Selecting the db filepath does not work with an absolute path. Maybe the relative path can be used.
            </Card.Footer>
        </Card>
        </div>
    );
};

export default SetFlatLocations;