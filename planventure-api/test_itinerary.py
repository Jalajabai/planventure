import unittest
from datetime import date

from utils.itinerary import MAX_ITINERARY_DAYS, generate_default_itinerary


class DefaultItineraryTests(unittest.TestCase):
    def test_one_entry_per_day_inclusive(self):
        itinerary = generate_default_itinerary(date(2027, 2, 27), date(2027, 3, 2))

        self.assertEqual([d['day'] for d in itinerary], [1, 2, 3, 4])
        self.assertEqual([d['date'] for d in itinerary],
                         ['2027-02-27', '2027-02-28', '2027-03-01', '2027-03-02'])
        self.assertEqual(itinerary[0], {
            'day': 1, 'date': '2027-02-27', 'title': 'Day 1', 'activities': [], 'notes': '',
        })

    def test_single_day_trip(self):
        self.assertEqual(len(generate_default_itinerary(date(2027, 5, 1), date(2027, 5, 1))), 1)

    def test_entries_do_not_share_mutable_state(self):
        itinerary = generate_default_itinerary(date(2027, 5, 1), date(2027, 5, 2))
        itinerary[0]['activities'].append('Museum')

        self.assertEqual(itinerary[1]['activities'], [])
        self.assertEqual(generate_default_itinerary(date(2027, 5, 1), date(2027, 5, 2))[0]['activities'], [])

    def test_invalid_or_oversized_ranges_give_empty_itinerary(self):
        self.assertEqual(generate_default_itinerary(date(2027, 5, 2), date(2027, 5, 1)), [])
        self.assertEqual(generate_default_itinerary(date(2027, 1, 1), date(9999, 12, 31)), [])

    def test_maximum_length_is_allowed(self):
        start = date(2027, 1, 1)
        end = date.fromordinal(start.toordinal() + MAX_ITINERARY_DAYS - 1)
        self.assertEqual(len(generate_default_itinerary(start, end)), MAX_ITINERARY_DAYS)
        self.assertEqual(generate_default_itinerary(start, date.fromordinal(end.toordinal() + 1)), [])


if __name__ == '__main__':
    unittest.main()
