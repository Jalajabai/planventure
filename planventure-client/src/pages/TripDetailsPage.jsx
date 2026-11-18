import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PropTypes from 'prop-types';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Button,
  Skeleton,
  Alert,
  Chip,
  Stack,
  Divider
} from '@mui/material';
import {
  AccessTime,
  LocationOn,
  Edit as EditIcon,
  ArrowBack as ArrowBackIcon
} from '@mui/icons-material';
import { tripService } from '../services/tripService';
import dayjs from 'dayjs';
import ItineraryDay from '../components/itinerary/ItineraryDay';
import { generateTemplateForDate } from '../data/itineraryTemplates';
import { slotsByDateFromApi, slotsByDateToApi, hasAnyActivities } from '../utils/itinerary';
import { toDateTimeInput } from '../utils/dateTime';
import EmptyItinerary from '../components/itinerary/EmptyItinerary';
import AccommodationCard from '../components/overview/AccommodationCard';
import TransportationCard from '../components/overview/TransportationCard';
import EmptyOverviewSection from '../components/overview/EmptyOverviewSection';
import { Add as AddIcon } from '@mui/icons-material';

const TabPanel = ({ children, value, index }) => (
  <div hidden={value !== index} style={{ padding: '24px 0' }}>
    {value === index && children}
  </div>
);

TabPanel.propTypes = {
  children: PropTypes.node,
  value: PropTypes.number.isRequired,
  index: PropTypes.number.isRequired,
};

const SaveStatus = ({ status }) => {
  if (status === 'idle') return null;
  return (
    <Typography
      variant="caption"
      color={status === 'error' ? 'error' : 'text.secondary'}
      role="status"
    >
      {status === 'saving' && 'Saving…'}
      {status === 'saved' && 'All changes saved'}
      {status === 'error' && "Couldn't save your latest change. It will retry on your next edit."}
    </Typography>
  );
};

SaveStatus.propTypes = {
  status: PropTypes.oneOf(['idle', 'saving', 'saved', 'error']).isRequired,
};

const TripDetailsPage = () => {
  const { tripId } = useParams();
  const navigate = useNavigate();
  const [trip, setTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [itinerary, setItinerary] = useState({});
  const [itineraryStarted, setItineraryStarted] = useState(false);
  const [saveStatus, setSaveStatus] = useState('idle');
  const itineraryRef = useRef({});
  const apiItineraryRef = useRef({});
  const saveQueueRef = useRef(Promise.resolve());
  const pendingSavesRef = useRef(0);
  const [accommodations, setAccommodations] = useState([]);
  const [transportation, setTransportation] = useState([]);
  const [accommodationDraft, setAccommodationDraft] = useState(null);
  const [transportDraft, setTransportDraft] = useState(null);
  const accommodationsRef = useRef([]);
  const transportationRef = useRef([]);

  useEffect(() => {
    const fetchTripDetails = async () => {
      try {
        setLoading(true);
        const response = await tripService.getTrip(tripId);

        if (!response || !response.trip) {
          throw new Error('Trip not found');
        }

        setTrip(response.trip);
        apiItineraryRef.current = response.trip.itinerary || {};
        const loadedItinerary = slotsByDateFromApi(response.trip.itinerary);
        itineraryRef.current = loadedItinerary;
        setItinerary(loadedItinerary);

        const loadedAccommodations = response.trip.accommodations || [];
        accommodationsRef.current = loadedAccommodations;
        setAccommodations(loadedAccommodations);
        const loadedTransportation = response.trip.transportation || [];
        transportationRef.current = loadedTransportation;
        setTransportation(loadedTransportation);
      } catch (err) {
        console.error('Error fetching trip:', err);
        setError(err.message || 'Failed to load trip details');
      } finally {
        setLoading(false);
      }
    };

    if (tripId) {
      fetchTripDetails();
    }
  }, [tripId]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Saves are chained so they reach the API in the order the edits were made
  const queueSave = (fields) => {
    pendingSavesRef.current += 1;
    setSaveStatus('saving');

    saveQueueRef.current = saveQueueRef.current
      .then(() => tripService.updateTrip(tripId, fields))
      .then(() => {
        pendingSavesRef.current -= 1;
        if (pendingSavesRef.current === 0) setSaveStatus('saved');
      })
      .catch(() => {
        pendingSavesRef.current -= 1;
        setSaveStatus('error');
      });
  };

  const persistItinerary = (slotsByDate) => {
    const payload = slotsByDateToApi(slotsByDate, apiItineraryRef.current);
    apiItineraryRef.current = payload;
    queueSave({ itinerary: payload });
  };

  const updateItinerary = (updater) => {
    const next = updater(itineraryRef.current);
    itineraryRef.current = next;
    setItinerary(next);
    persistItinerary(next);
  };

  const handleAddSlot = (date, newSlot) => {
    updateItinerary(prev => ({
      ...prev,
      [date]: [...(prev[date] || []), newSlot]
    }));
  };

  const handleUpdateSlot = (date, updatedSlot) => {
    updateItinerary(prev => ({
      ...prev,
      [date]: (prev[date] || []).map(slot => 
        slot.id === updatedSlot.id ? updatedSlot : slot
      )
    }));
  };

  const handleDeleteSlot = (date, slotId) => {
    updateItinerary(prev => ({
      ...prev,
      [date]: (prev[date] || []).filter(slot => slot.id !== slotId)
    }));
  };

  const handleCreateEmptyItinerary = () => {
    const dates = getDatesArray(trip.start_date, trip.end_date);
    const emptyItinerary = dates.reduce((acc, date) => {
      acc[date] = [];
      return acc;
    }, {});
    setItineraryStarted(true);
    updateItinerary(() => emptyItinerary);
  };

  const handleUseTemplate = () => {
    const dates = getDatesArray(trip.start_date, trip.end_date);
    const templateItinerary = dates.reduce((acc, date) => {
      acc[date] = generateTemplateForDate(date);
      return acc;
    }, {});
    setItineraryStarted(true);
    updateItinerary(() => templateItinerary);
  };

  const updateOverviewList = (listRef, setList, field, updater) => {
    const next = updater(listRef.current);
    listRef.current = next;
    setList(next);
    queueSave({ [field]: next });
  };

  const upsert = (list, item) => (
    list.some(existing => existing.id === item.id)
      ? list.map(existing => (existing.id === item.id ? item : existing))
      : [...list, item]
  );

  const startAccommodationDraft = () => {
    setAccommodationDraft({
      id: Date.now(),
      name: '',
      address: '',
      checkIn: toDateTimeInput(trip.start_date, 15),
      checkOut: toDateTimeInput(trip.end_date, 11),
      bookingRef: ''
    });
  };

  const saveAccommodation = (item) => {
    updateOverviewList(accommodationsRef, setAccommodations, 'accommodations', list => upsert(list, item));
    setAccommodationDraft(null);
  };

  const deleteAccommodation = (id) => {
    updateOverviewList(accommodationsRef, setAccommodations, 'accommodations', list => list.filter(item => item.id !== id));
  };

  const startTransportDraft = () => {
    setTransportDraft({
      id: Date.now(),
      type: 'flight',
      from: '',
      to: '',
      departure: toDateTimeInput(trip.start_date, 9),
      arrival: toDateTimeInput(trip.start_date, 12),
      bookingRef: ''
    });
  };

  const saveTransport = (item) => {
    updateOverviewList(transportationRef, setTransportation, 'transportation', list => upsert(list, item));
    setTransportDraft(null);
  };

  const deleteTransport = (id) => {
    updateOverviewList(transportationRef, setTransportation, 'transportation', list => list.filter(item => item.id !== id));
  };

  if (loading) {
    return (
      <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
        <Skeleton variant="text" height={40} width={200} />
        <Skeleton variant="rectangular" height={200} sx={{ mt: 2 }} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
        <Alert 
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={() => navigate('/dashboard')}>
              Back to Dashboard
            </Button>
          }
        >
          {error}
        </Alert>
      </Box>
    );
  }

  if (!trip) {
    return (
      <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
        <Alert severity="error">
          Trip not found
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/dashboard')}
        sx={{ mb: 3 }}
      >
        Back to Dashboard
      </Button>

      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
          <Box>
            <Typography variant="h4" gutterBottom>
              {trip.title || trip.destination}
            </Typography>
            <Stack direction="row" spacing={2} alignItems="center">
              <Chip
                icon={<LocationOn />}
                label={trip.destination}
                color="primary"
                variant="outlined"
              />
              <Chip
                icon={<AccessTime />}
                label={`${dayjs(trip.start_date).format('MMM D')} - ${dayjs(trip.end_date).format('MMM D, YYYY')}`}
                variant="outlined"
              />
            </Stack>
          </Box>
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={() => navigate(`/trips/${tripId}/edit`)}
          >
            Edit Trip
          </Button>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Tabs value={tabValue} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="Overview" />
          <Tab label="Itinerary" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', minHeight: 20, mb: 1 }}>
              <SaveStatus status={saveStatus} />
            </Box>
            <Box sx={{ mb: 4 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Accommodations</Typography>
                {accommodations.length > 0 && (
                  <Button
                    startIcon={<AddIcon />}
                    onClick={startAccommodationDraft}
                    disabled={Boolean(accommodationDraft)}
                  >
                    Add Accommodation
                  </Button>
                )}
              </Box>
              
              {accommodations.length === 0 && !accommodationDraft ? (
                <EmptyOverviewSection
                  title="Accommodations"
                  description="Add details about where you'll be staying during your trip, including hotels, rentals, or other lodging arrangements."
                  onAdd={startAccommodationDraft}
                />
              ) : (
                <>
                  {accommodations.map(accommodation => (
                    <AccommodationCard
                      key={accommodation.id}
                      accommodation={accommodation}
                      onUpdate={saveAccommodation}
                      onDelete={deleteAccommodation}
                    />
                  ))}
                  {accommodationDraft && (
                    <AccommodationCard
                      key={accommodationDraft.id}
                      accommodation={accommodationDraft}
                      isNew
                      onUpdate={saveAccommodation}
                      onCancel={() => setAccommodationDraft(null)}
                    />
                  )}
                </>
              )}
            </Box>

            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Transportation</Typography>
                {transportation.length > 0 && (
                  <Button
                    startIcon={<AddIcon />}
                    onClick={startTransportDraft}
                    disabled={Boolean(transportDraft)}
                  >
                    Add Transportation
                  </Button>
                )}
              </Box>
              
              {transportation.length === 0 && !transportDraft ? (
                <EmptyOverviewSection
                  title="Transportation"
                  description="Add your travel arrangements including flights, trains, rental cars, or other modes of transportation."
                  onAdd={startTransportDraft}
                />
              ) : (
                <>
                  {transportation.map(transport => (
                    <TransportationCard
                      key={transport.id}
                      transport={transport}
                      onUpdate={saveTransport}
                      onDelete={deleteTransport}
                    />
                  ))}
                  {transportDraft && (
                    <TransportationCard
                      key={transportDraft.id}
                      transport={transportDraft}
                      isNew
                      onUpdate={saveTransport}
                      onCancel={() => setTransportDraft(null)}
                    />
                  )}
                </>
              )}
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6" gutterBottom>
                Itinerary
              </Typography>
              <SaveStatus status={saveStatus} />
            </Box>
            {!itineraryStarted && !hasAnyActivities(itinerary) ? (
              <EmptyItinerary
                onCreateEmpty={handleCreateEmptyItinerary}
                onUseTemplate={handleUseTemplate}
              />
            ) : (
              trip && getDatesArray(trip.start_date, trip.end_date).map(date => (
                <ItineraryDay
                  key={date}
                  date={date}
                  slots={itinerary[date] || []}
                  onAddSlot={handleAddSlot}
                  onUpdateSlot={handleUpdateSlot}
                  onDeleteSlot={handleDeleteSlot}
                />
              ))
            )}
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  );
};

// Helper function to generate dates array
const getDatesArray = (startDate, endDate) => {
  const dates = [];
  let currentDate = dayjs(startDate);
  const lastDate = dayjs(endDate);

  while (currentDate.isBefore(lastDate) || currentDate.isSame(lastDate, 'day')) {
    dates.push(currentDate.format('YYYY-MM-DD'));
    currentDate = currentDate.add(1, 'day');
  }

  return dates;
};

export default TripDetailsPage;
