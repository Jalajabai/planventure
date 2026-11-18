import dayjs from 'dayjs';

// Value format used by <input type="datetime-local">
const INPUT_FORMAT = 'YYYY-MM-DDTHH:mm';

export const formatDateTime = (value) => {
  const parsed = dayjs(value);
  return value && parsed.isValid() ? parsed.format('MMM D, YYYY h:mm A') : 'Not set';
};

// A datetime-local value on the given date (falls back to today) at hour:minute, in local time
export const toDateTimeInput = (date, hour, minute = 0) => {
  const base = dayjs(date).isValid() ? dayjs(date) : dayjs();
  return base.hour(hour).minute(minute).format(INPUT_FORMAT);
};

// datetime-local strings share one fixed-width format, so they compare correctly as text
export const isEndBeforeStart = (start, end) => Boolean(start && end && end < start);
