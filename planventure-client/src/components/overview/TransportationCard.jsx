import { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  IconButton,
  Button,
  TextField,
  Stack,
  MenuItem
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import PropTypes from 'prop-types';
import { formatDateTime, isEndBeforeStart } from '../../utils/dateTime';

const TransportationCard = ({ transport, onUpdate, onDelete, isNew = false, onCancel }) => {
  const [isEditing, setIsEditing] = useState(isNew);
  const [editedData, setEditedData] = useState(transport);

  const arrivalError = isEndBeforeStart(editedData.departure, editedData.arrival);
  const isValid = Boolean(editedData.from?.trim() && editedData.to?.trim()) && !arrivalError;

  const handleSave = () => {
    onUpdate({ ...editedData, from: editedData.from.trim(), to: editedData.to.trim() });
    setIsEditing(false);
  };

  const handleCancel = () => {
    if (isNew) {
      onCancel();
      return;
    }
    setEditedData(transport);
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Stack spacing={2}>
            <TextField
              select
              fullWidth
              label="Type"
              value={editedData.type}
              onChange={(e) => setEditedData({ ...editedData, type: e.target.value })}
            >
              <MenuItem value="flight">Flight</MenuItem>
              <MenuItem value="train">Train</MenuItem>
              <MenuItem value="bus">Bus</MenuItem>
              <MenuItem value="car">Car Rental</MenuItem>
            </TextField>
            <TextField
              fullWidth
              required
              label="From"
              value={editedData.from}
              onChange={(e) => setEditedData({ ...editedData, from: e.target.value })}
              autoFocus={isNew}
            />
            <TextField
              fullWidth
              required
              label="To"
              value={editedData.to}
              onChange={(e) => setEditedData({ ...editedData, to: e.target.value })}
            />
            <TextField
              fullWidth
              label="Departure"
              type="datetime-local"
              value={editedData.departure}
              onChange={(e) => setEditedData({ ...editedData, departure: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              fullWidth
              label="Arrival"
              type="datetime-local"
              value={editedData.arrival}
              onChange={(e) => setEditedData({ ...editedData, arrival: e.target.value })}
              InputLabelProps={{ shrink: true }}
              error={arrivalError}
              helperText={arrivalError ? 'Arrival must be after departure' : ''}
            />
            <TextField
              fullWidth
              label="Booking Reference"
              value={editedData.bookingRef}
              onChange={(e) => setEditedData({ ...editedData, bookingRef: e.target.value })}
            />
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
              <Button startIcon={<CancelIcon />} onClick={handleCancel}>
                Cancel
              </Button>
              <Button
                startIcon={<SaveIcon />}
                variant="contained"
                onClick={handleSave}
                disabled={!isValid}
              >
                Save
              </Button>
            </Box>
          </Stack>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h6" gutterBottom>
              {transport.type.charAt(0).toUpperCase() + transport.type.slice(1)}
            </Typography>
            <Typography color="text.secondary" gutterBottom>
              {transport.from} → {transport.to}
            </Typography>
            <Typography variant="body2" gutterBottom>
              Departure: {formatDateTime(transport.departure)}
            </Typography>
            <Typography variant="body2" gutterBottom>
              Arrival: {formatDateTime(transport.arrival)}
            </Typography>
            {transport.bookingRef && (
              <Typography variant="body2">
                Booking Reference: {transport.bookingRef}
              </Typography>
            )}
          </Box>
          <Box>
            <IconButton onClick={() => setIsEditing(true)} aria-label="Edit transportation">
              <EditIcon />
            </IconButton>
            <IconButton
              onClick={() => onDelete(transport.id)}
              color="error"
              aria-label="Delete transportation"
            >
              <DeleteIcon />
            </IconButton>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

TransportationCard.propTypes = {
  transport: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.number, PropTypes.string]).isRequired,
    type: PropTypes.string.isRequired,
    from: PropTypes.string,
    to: PropTypes.string,
    departure: PropTypes.string,
    arrival: PropTypes.string,
    bookingRef: PropTypes.string,
  }).isRequired,
  onUpdate: PropTypes.func.isRequired,
  onDelete: PropTypes.func,
  isNew: PropTypes.bool,
  onCancel: PropTypes.func,
};

export default TransportationCard;
