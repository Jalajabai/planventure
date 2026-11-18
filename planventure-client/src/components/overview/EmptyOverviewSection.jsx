import {
  Box,
  Typography,
  Button,
  Paper
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';

import PropTypes from 'prop-types';

const EmptyOverviewSection = ({ title, description, onAdd }) => {
  return (
    <Paper 
      sx={{ 
        p: 3, 
        textAlign: 'center',
        bgcolor: 'background.default',
        mb: 2
      }}
    >
      <Typography variant="h6" gutterBottom>
        No {title} Added Yet
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {description}
      </Typography>
      <Button
        variant="outlined"
        startIcon={<AddIcon />}
        onClick={onAdd}
      >
        Add {title}
      </Button>
    </Paper>
  );
};

EmptyOverviewSection.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  onAdd: PropTypes.func.isRequired,
};

export default EmptyOverviewSection;
