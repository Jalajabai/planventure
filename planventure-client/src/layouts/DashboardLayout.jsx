import { useState } from 'react';
import {
  Box,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Toolbar,
  Divider,
  Typography,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Map as MapIcon,
  AddCircleOutline as AddIcon,
  ListAlt as ListAltIcon,
  Settings as SettingsIcon,
  ChevronLeft as ChevronLeftIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';
import Navbar from '../components/navigation/Navbar';
import Footer from '../components/navigation/Footer';

const DRAWER_WIDTH = 240;
// Footer is fixed to the viewport bottom, so content and the drawer must clear it
const FOOTER_CLEARANCE = 12;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'My Trips', icon: <MapIcon />, path: '/trips', matchSubpaths: true },
  { text: 'New Trip', icon: <AddIcon />, path: '/trips/new' },
  { text: 'Trip Planner', icon: <ListAltIcon />, path: '/planner', comingSoon: true },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings', comingSoon: true },
];

const isActive = (item, pathname) => {
  if (pathname === item.path) return true;
  // Trip pages (details/edit) belong to "My Trips", but "New Trip" has its own entry
  return Boolean(item.matchSubpaths)
    && pathname.startsWith(`${item.path}/`)
    && pathname !== '/trips/new';
};

const DashboardLayout = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const toggleDrawer = () => setMobileOpen((open) => !open);

  const handleNavigate = (path) => {
    navigate(path);
    setMobileOpen(false);
  };

  const sidebar = (showClose) => (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {showClose ? (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 2 }}>
          <Typography variant="h6" component="div">Planventure</Typography>
          <IconButton onClick={toggleDrawer} aria-label="close drawer">
            <ChevronLeftIcon />
          </IconButton>
        </Box>
      ) : (
        // Pushes the list below the fixed navbar
        <Toolbar />
      )}
      <Divider />
      <List sx={{ flexGrow: 1, overflowY: 'auto', pb: showClose ? 2 : FOOTER_CLEARANCE }}>
        {menuItems.map((item) => {
          const selected = isActive(item, pathname);
          return (
            <ListItemButton
              key={item.text}
              selected={selected}
              disabled={item.comingSoon}
              onClick={() => handleNavigate(item.path)}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'primary.light',
                  color: 'primary.contrastText',
                  '&:hover': { backgroundColor: 'primary.light' },
                },
              }}
            >
              <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                secondary={item.comingSoon ? 'Coming soon' : undefined}
              />
            </ListItemButton>
          );
        })}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: 'background.default' }}>
      <Navbar>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={toggleDrawer}
          sx={{ mr: 2, display: { sm: 'none' } }}
        >
          <MenuIcon />
        </IconButton>
      </Navbar>
      <Toolbar />

      <Box sx={{ display: 'flex', flexGrow: 1 }}>
        <Box component="nav" aria-label="Dashboard navigation" sx={{ width: { sm: DRAWER_WIDTH }, flexShrink: { sm: 0 } }}>
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={toggleDrawer}
            ModalProps={{ keepMounted: true }}
            sx={{
              display: { xs: 'block', sm: 'none' },
              '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH },
            }}
          >
            {sidebar(true)}
          </Drawer>

          <Drawer
            variant="permanent"
            open
            sx={{
              display: { xs: 'none', sm: 'block' },
              // Sit below the footer (z-index 1000) rather than covering it
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: DRAWER_WIDTH,
                zIndex: 999,
              },
            }}
          >
            {sidebar(false)}
          </Drawer>
        </Box>

        <Box
          component="main"
          sx={{
            flexGrow: 1,
            minWidth: 0,
            p: 3,
            pb: FOOTER_CLEARANCE,
          }}
        >
          {children}
        </Box>
      </Box>

      <Footer />
    </Box>
  );
};

DashboardLayout.propTypes = {
  children: PropTypes.node.isRequired,
};

export default DashboardLayout;
