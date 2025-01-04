import React, { useState, useEffect } from 'react';
import { Card, CardHeader, Button } from 'react-bootstrap';
import DataTable from 'react-data-table-component';
import { Pencil, Trash, Save, X } from 'react-bootstrap-icons';
import { socket } from './socket';

const SetFlatLocations = () => {
    const [flats, setFlats] = useState([]);
    const [editableRows, setEditableRows] = useState({});
    const [editData, setEditData] = useState({});

    useEffect(() => {
        socket.emit('/api/get-flat-locations');
        
        socket.on('flat_locations', (data) => {
            setFlats(Object.entries(data).map(([name, details]) => ({
                name,
                street: details.street || '',
                number: details.streetnumber || '',
                postcode: details.plz || '',
                state: details.state || ''
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
                        className="me-2"
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
        <Card>
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
    );
};

export default SetFlatLocations;