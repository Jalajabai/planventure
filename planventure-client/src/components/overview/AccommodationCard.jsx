import { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  IconButton,
  Button,
  TextField,
  Stack
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import PropTypes from 'prop-types';
import { formatDateTime, isEndBeforeStart } from '../../utils/dateTime';

const AccommodationCard = ({ accommodation, onUpdate, onDelete, isNew = false, onCancel }) => {
  const [isEditing, setIsEditing] = useState(isNew);
  const [editedData, setEditedData] = useState(accommodation);

  const checkOutError = isEndBeforeStart(editedData.checkIn, editedData.checkOut);
  const isValid = Boolean(editedData.name?.trim()) && !checkOutError;

  const handleSave = () => {
    onUpdate({ ...editedData, name: editedData.name.trim() });
    setIsEditing(false);
  };

  const handleCancel = () => {
    if (isNew) {
      onCancel();
      return;
    }
    setEditedData(accommodation);
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Stack spacing={2}>
            <TextField
              fullWidth
              required
              label="Name"
              value={editedData.name}
              onChange={(e) => setEditedData({ ...editedData, name: e.target.value })}
              autoFocus={isNew}
            />
            <TextField
              fullWidth
              label="Address"
              value={editedData.address}
              onChange={(e) => setEditedData({ ...editedData, address: e.target.value })}
            />
            <TextField
              fullWidth
              label="Check-in"
              type="datetime-local"
              value={editedData.checkIn}
              onChange={(e) => setEditedData({ ...editedData, checkIn: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              fullWidth
              label="Check-out"
              type="datetime-local"
              value={editedData.checkOut}
              onChange={(e) => setEditedData({ ...editedData, checkOut: e.target.value })}
              InputLabelProps={{ shrink: true }}
              error={checkOutError}
              helperText={checkOutError ? 'Check-out must be after check-in' : ''}
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
              {accommodation.name}
            </Typography>
            {accommodation.address && (
              <Typography color="text.secondary" gutterBottom>
                {accommodation.address}
              </Typography>
            )}
            <Typography variant="body2" gutterBottom>
              Check-in: {formatDateTime(accommodation.checkIn)}
            </Typography>
            <Typography variant="body2" gutterBottom>
              Check-out: {formatDateTime(accommodation.checkOut)}
            </Typography>
            {accommodation.bookingRef && (
              <Typography variant="body2">
                Booking Reference: {accommodation.bookingRef}
              </Typography>
            )}
          </Box>
          <Box>
            <IconButton onClick={() => setIsEditing(true)} aria-label="Edit accommodation">
              <EditIcon />
            </IconButton>
            <IconButton
              onClick={() => onDelete(accommodation.id)}
              color="error"
              aria-label="Delete accommodation"
            >
              <DeleteIcon />
            </IconButton>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

AccommodationCard.propTypes = {
  accommodation: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.number, PropTypes.string]).isRequired,
    name: PropTypes.string,
    address: PropTypes.string,
    checkIn: PropTypes.string,
    checkOut: PropTypes.string,
    bookingRef: PropTypes.string,
  }).isRequired,
  onUpdate: PropTypes.func.isRequired,
  onDelete: PropTypes.func,
  isNew: PropTypes.bool,
  onCancel: PropTypes.func,
};

export default AccommodationCard;
