// The API stores one object per day: { activities: [...], meals, accommodation, transportation, notes }.
// The UI works with a flat { 'YYYY-MM-DD': [slot, ...] } map, so these helpers convert between the two
// without dropping the per-day fields the UI doesn't edit.

const createEmptyDay = () => ({
  activities: [],
  meals: {
    breakfast: { time: '08:00', place: '', notes: '' },
    lunch: { time: '13:00', place: '', notes: '' },
    dinner: { time: '19:00', place: '', notes: '' }
  },
  accommodation: { name: '', address: '', check_in: '', check_out: '', confirmation: '' },
  transportation: [],
  notes: ''
});

export const slotsByDateFromApi = (apiItinerary) => {
  const slotsByDate = {};
  Object.entries(apiItinerary || {}).forEach(([date, day]) => {
    slotsByDate[date] = Array.isArray(day) ? day : (day?.activities || []);
  });
  return slotsByDate;
};

export const slotsByDateToApi = (slotsByDate, apiItinerary) => {
  const result = { ...(apiItinerary || {}) };
  Object.entries(slotsByDate).forEach(([date, slots]) => {
    const existingDay = result[date];
    const baseDay = existingDay && !Array.isArray(existingDay) ? existingDay : createEmptyDay();
    result[date] = { ...baseDay, activities: slots };
  });
  return result;
};

export const hasAnyActivities = (slotsByDate) =>
  Object.values(slotsByDate).some((slots) => slots.length > 0);
