import { useState, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  Typography, 
  Alert,
  Paper
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import { useNavigate } from 'react-router-dom';
import PropTypes from 'prop-types';
import { tripService } from '../../services/tripService';

const EditTripForm = ({ trip }) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    title: trip?.title || '',
    destination: trip?.destination || '',
    startDate: trip?.start_date ? dayjs(trip.start_date) : dayjs(),
    endDate: trip?.end_date ? dayjs(trip.end_date) : dayjs().add(1, 'day')
  });

  // Add useEffect to update form data when trip prop changes
  useEffect(() => {
    if (trip) {
      setFormData({
        title: trip.title || '',
        destination: trip.destination || '',
        startDate: dayjs(trip.start_date),
        endDate: dayjs(trip.end_date)
      });
    }
  }, [trip]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const tripData = {
        title: formData.title,
        destination: formData.destination,
        start_date: formData.startDate.format('YYYY-MM-DD'),
        end_date: formData.endDate.format('YYYY-MM-DD'),
      };

      await tripService.updateTrip(trip.id, tripData);
      navigate(`/trips/${trip.id}`);
    } catch (err) {
      setError(err.message || 'Failed to update trip');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Pickers yield null (cleared) or an invalid dayjs (partial input), so check before comparing
  const hasValidDates = () => {
    return Boolean(formData.startDate?.isValid() && formData.endDate?.isValid());
  };

  const getDateError = () => {
    if (!hasValidDates()) return 'Please enter valid start and end dates';
    if (formData.endDate.isBefore(formData.startDate, 'day')) return 'End date must be after start date';
    return '';
  };

  const dateError = getDateError();

  const isFormValid = () => {
    return formData.title?.trim() && 
           formData.destination?.trim() && 
           !dateError &&
           !loading;
  };

  return (
    <Paper elevation={2} sx={{ p: 4, maxWidth: 600, mx: 'auto', mt: 4 }}>
      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 3
        }}
      >
        <Typography variant="h5" component="h1" gutterBottom>
          Edit Trip
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <TextField
          fullWidth
          label="Trip Title"
          name="title"
          value={formData.title}
          onChange={handleChange}
          required
        />

        <TextField
          fullWidth
          label="Destination"
          name="destination"
          value={formData.destination}
          onChange={handleChange}
          required
        />

        <LocalizationProvider dateAdapter={AdapterDayjs}>
          <DatePicker
            label="Start Date"
            value={formData.startDate}
            onChange={(newValue) => {
              setFormData(prev => ({ ...prev, startDate: newValue }));
            }}
            slotProps={{
              textField: { fullWidth: true }
            }}
          />

          <DatePicker
            label="End Date"
            value={formData.endDate}
            onChange={(newValue) => {
              setFormData(prev => ({ ...prev, endDate: newValue }));
            }}
            minDate={formData.startDate?.isValid() ? formData.startDate : undefined}
            slotProps={{
              textField: { 
                fullWidth: true,
                error: Boolean(dateError),
                helperText: dateError
              }
            }}
          />
        </LocalizationProvider>

        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <Button
            type="button"
            variant="outlined"
            onClick={() => navigate(`/trips/${trip.id}`)}
            sx={{ flex: 1 }}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={!isFormValid()}
            sx={{ flex: 1 }}
          >
            {loading ? 'Saving...' : 'Save Changes'}
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};

EditTripForm.propTypes = {
  trip: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
    title: PropTypes.string,
    destination: PropTypes.string,
    start_date: PropTypes.string,
    end_date: PropTypes.string,
  }),
};

export default EditTripForm;
