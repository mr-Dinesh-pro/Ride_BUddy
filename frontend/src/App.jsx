import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// Coordinates of Hyderabad Areas for plotting the interactive SVG Map
const LOCATION_COORDS = {
  "Miyapur": [17.4968, 78.3614],
  "Kukatpally": [17.4875, 78.3953],
  "Moosapet": [17.4690, 78.4190],
  "Ameerpet": [17.4374, 78.4482],
  "SR Nagar": [17.4429, 78.4414],
  "Begumpet": [17.4448, 78.4651],
  "Punjagutta": [17.4265, 78.4531],
  "Somajiguda": [17.4263, 78.4593],
  "Hitech City": [17.4483, 78.3741],
  "Madhapur": [17.4485, 78.3908],
  "Jubilee Hills": [17.4300, 78.4000],
  "Banjara Hills": [17.4165, 78.4200],
  "Gachibowli": [17.4401, 78.3489],
  "Kondapur": [17.4699, 78.3578],
  "Nanakramguda": [17.4172, 78.3473],
  "Financial District": [17.4180, 78.3375],
  "Manikonda": [17.4042, 78.3846],
  "Mehdipatnam": [17.3916, 78.4430],
  "Tolichowki": [17.3980, 78.4162],
  "Secunderabad": [17.4399, 78.4983],
  "Uppal": [17.4022, 78.5601],
  "LB Nagar": [17.3460, 78.5510],
  "Dilsukhnagar": [17.3688, 78.5247],
  "Kothapet": [17.3715, 78.5350],
  "Habsiguda": [17.4071, 78.5312],
  "Charminar": [17.3616, 78.4747],
  "Koti": [17.3824, 78.4842],
  "Tarnaka": [17.4277, 78.5385],
  "Yusufguda": [17.4367, 78.4239],
  "Khairatabad": [17.4124, 78.4608]
};

// Transit connections to draw network background grid lines
const MAP_EDGES = [
  ["Miyapur", "Kukatpally"], ["Kukatpally", "Moosapet"], ["Moosapet", "Ameerpet"], ["Ameerpet", "SR Nagar"],
  ["SR Nagar", "Yusufguda"], ["Yusufguda", "Jubilee Hills"], ["Jubilee Hills", "Madhapur"], ["Madhapur", "Hitech City"],
  ["Hitech City", "Gachibowli"], ["Gachibowli", "Nanakramguda"], ["Nanakramguda", "Financial District"],
  ["Secunderabad", "Begumpet"], ["Begumpet", "Somajiguda"], ["Somajiguda", "Punjagutta"], ["Punjagutta", "Khairatabad"],
  ["Khairatabad", "Banjara Hills"], ["Banjara Hills", "Jubilee Hills"],
  ["Uppal", "Habsiguda"], ["Habsiguda", "Tarnaka"], ["Tarnaka", "Secunderabad"], ["Ameerpet", "Yusufguda"],
  ["Madhapur", "Kondapur"], ["Kondapur", "Gachibowli"],
  ["LB Nagar", "Kothapet"], ["Kothapet", "Dilsukhnagar"], ["Dilsukhnagar", "Koti"], ["Koti", "Charminar"],
  ["Charminar", "Mehdipatnam"], ["Mehdipatnam", "Tolichowki"], ["Tolichowki", "Manikonda"], ["Manikonda", "Gachibowli"],
  ["Gachibowli", "Financial District"],
  ["Kondapur", "Miyapur"], ["Kondapur", "Madhapur"], ["Kondapur", "Hitech City"], ["Manikonda", "Gachibowli"],
  ["Tolichowki", "Mehdipatnam"], ["Banjara Hills", "Punjagutta"], ["Somajiguda", "Begumpet"], ["SR Nagar", "Ameerpet"],
  ["Ameerpet", "Punjagutta"], ["Punjagutta", "Banjara Hills"], ["Koti", "Dilsukhnagar"], ["Charminar", "Koti"]
];

function InteractiveMap({ startNode, endNode, routePath }) {
  const minLat = 17.34;
  const maxLat = 17.51;
  const minLng = 78.33;
  const maxLng = 78.57;

  const getSvgCoords = (name) => {
    const coords = LOCATION_COORDS[name];
    if (!coords) return { x: 0, y: 0 };
    const [lat, lng] = coords;
    const padding = 40;
    const width = 600;
    const height = 400;
    const x = padding + ((lng - minLng) / (maxLng - minLng)) * (width - 2 * padding);
    const y = height - padding - ((lat - minLat) / (maxLat - minLat)) * (height - 2 * padding);
    return { x, y };
  };

  return (
    <div className="map-container">
      <svg viewBox="0 0 600 400" className="map-svg">
        {/* Draw background grid lines */}
        {MAP_EDGES.map(([u, v], idx) => {
          const p1 = getSvgCoords(u);
          const p2 = getSvgCoords(v);
          return (
            <line 
              key={`edge-${idx}`} 
              x1={p1.x} y1={p1.y} 
              x2={p2.x} y2={p2.y} 
              className="map-edge" 
            />
          );
        })}

        {/* Draw highlighted active route */}
        {routePath && routePath.length > 1 && 
          routePath.map((node, i) => {
            if (i === routePath.length - 1) return null;
            const p1 = getSvgCoords(node);
            const p2 = getSvgCoords(routePath[i + 1]);
            return (
              <line 
                key={`path-edge-${i}`} 
                x1={p1.x} y1={p1.y} 
                x2={p2.x} y2={p2.y} 
                className="map-edge-highlight" 
              />
            );
          })
        }

        {/* Draw coordinates nodes */}
        {Object.keys(LOCATION_COORDS).map((name) => {
          const { x, y } = getSvgCoords(name);
          let nodeClass = "map-node";
          if (name === startNode) nodeClass = "map-node-start";
          else if (name === endNode) nodeClass = "map-node-end";
          else if (routePath && routePath.includes(name)) nodeClass = "map-node-highlight";

          const isHighlight = name === startNode || name === endNode || (routePath && routePath.includes(name));

          return (
            <g key={`node-group-${name}`}>
              <circle cx={x} cy={y} r={isHighlight ? 7 : 4.5} className={nodeClass} />
              {isHighlight && (
                <text x={x} y={y - 12} className="map-label map-label-highlight">
                  {name}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function App() {
  // Navigation State (Hash-based Routing)
  const [currentRoute, setCurrentRoute] = useState(window.location.hash || '#/');
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user');
    return saved ? JSON.parse(saved) : null;
  });

  // DB and locations state
  const [locations, setLocations] = useState([]);
  const [dbStatus, setDbStatus] = useState('Checking...');
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [loading, setLoading] = useState(false);

  // Forms states
  const [loginForm, setLoginForm] = useState({ phone: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ name: '', phone: '', password: '', role: 'RIDER' });
  const [rideForm, setRideForm] = useState({ start: '', end: '', time: '', available_seats: 3 });
  const [searchForm, setSearchForm] = useState({ start: '', end: '' });

  // Data lists states
  const [searchResults, setSearchResults] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [driverBookings, setDriverBookings] = useState([]);
  const [smsMessages, setSmsMessages] = useState([]);
  const [selectedRide, setSelectedRide] = useState(null);

  // New WebSocket & Notification states
  const [notifications, setNotifications] = useState(() => {
    const saved = localStorage.getItem('notifications');
    return saved ? JSON.parse(saved) : [];
  });
  const [toasts, setToasts] = useState([]);
  const [showNotificationsDropdown, setShowNotificationsDropdown] = useState(false);

  // Ref to selectedRide to avoid stale closures in WebSockets onmessage
  const selectedRideRef = useRef(selectedRide);
  useEffect(() => {
    selectedRideRef.current = selectedRide;
  }, [selectedRide]);

  // Sync hash routing
  useEffect(() => {
    const handleHashChange = () => {
      setCurrentRoute(window.location.hash || '#/');
      setErrorMsg(null);
      setSuccessMsg(null);
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Set user dashboard access guard
  useEffect(() => {
    if (user) {
      if (currentRoute === '#/login' || currentRoute === '#/register') {
        window.location.hash = '#/rider';
      }
    } else {
      if (currentRoute !== '#/' && currentRoute !== '#/login' && currentRoute !== '#/register') {
        window.location.hash = '#/';
      }
    }
  }, [user, currentRoute]);

  // Fetch initial location data
  const fetchLocations = async () => {
    try {
      const res = await fetch('/api/locations');
      if (res.ok) {
        const data = await res.json();
        setLocations(data);
        setDbStatus('Online');
      } else {
        setDbStatus('Offline');
      }
    } catch {
      setDbStatus('Offline');
    }
  };

  useEffect(() => {
    fetchLocations();
  }, []);

  // Fetch bookings on dashboard loads
  const loadBookings = async () => {
    if (!user) return;
    try {
      const res = await fetch('/api/bookings', {
        headers: { 'X-User-Id': user.id }
      });
      if (res.ok) {
        const data = await res.json();
        setBookings(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadDriverBookings = async () => {
    if (!user) return;
    try {
      const res = await fetch('/api/driver/bookings', {
        headers: { 'X-User-Id': user.id }
      });
      if (res.ok) {
        const data = await res.json();
        setDriverBookings(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadMessages = async () => {
    if (!user) return;
    try {
      const res = await fetch('/api/messages', {
        headers: { 'X-User-Id': user.id }
      });
      if (res.ok) {
        const data = await res.json();
        setSmsMessages(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (user) {
      loadBookings();
      loadDriverBookings();
      if (currentRoute === '#/messages') {
        loadMessages();
      }
    }
  }, [user, currentRoute]);

  // Auth Operations
  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registerForm)
      });
      const data = await res.json();
      if (res.ok) {
        setUser(data);
        localStorage.setItem('user', JSON.stringify(data));
        setSuccessMsg("Registration successful!");
        window.location.hash = '#/rider';
      } else {
        setErrorMsg(data.detail || "Registration failed.");
      }
    } catch {
      setErrorMsg("Network error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm)
      });
      const data = await res.json();
      if (res.ok) {
        setUser(data);
        localStorage.setItem('user', JSON.stringify(data));
        window.location.hash = '#/rider';
      } else {
        setErrorMsg(data.detail || "Invalid phone or password.");
      }
    } catch {
      setErrorMsg("Network error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
    setLoginForm({ phone: '', password: '' });
    window.location.hash = '#/';
  };

  // Driver commutes offers
  const handleOfferRide = async (e) => {
    e.preventDefault();
    if (!rideForm.start || !rideForm.end || !rideForm.time) {
      setErrorMsg("Please fill out all fields.");
      return;
    }
    if (rideForm.start === rideForm.end) {
      setErrorMsg("Start and end locations must be different.");
      return;
    }
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch('/api/create-ride', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-User-Id': user.id
        },
        body: JSON.stringify(rideForm)
      });
      const data = await res.json();
      if (res.ok) {
        setSuccessMsg(`Ride offered successfully starting from ${data.ride_start}!`);
        setRideForm({ start: '', end: '', time: '', available_seats: 3 });
        loadBookings();
        loadDriverBookings();
        loadMessages();
      } else {
        setErrorMsg(data.detail || "Failed to publish ride offer.");
      }
    } catch {
      setErrorMsg("Network error occurred.");
    } finally {
      setLoading(false);
    }
  };

  // Rider searches matching driver overlaps
  const handleSearchRides = async (e) => {
    e.preventDefault();
    if (!searchForm.start || !searchForm.end) {
      setErrorMsg("Please select both start and end locations.");
      return;
    }
    if (searchForm.start === searchForm.end) {
      setErrorMsg("Start and destination must be different.");
      return;
    }
    setLoading(true);
    setErrorMsg(null);
    setSearchResults([]);
    setRoutes([]);
    try {
      // 1. Fetch matching overlapping rides
      const res = await fetch(`/api/find-rides?start=${encodeURIComponent(searchForm.start)}&end=${encodeURIComponent(searchForm.end)}`, {
        headers: { 'X-User-Id': user.id }
      });
      const data = await res.json();
      if (res.ok) {
        setSearchResults(data);
      } else {
        setErrorMsg(data.detail || "Search query failed.");
      }

      // 2. Fetch multi-hop route corridors
      const routeRes = await fetch(`/api/routes?start=${encodeURIComponent(searchForm.start)}&end=${encodeURIComponent(searchForm.end)}`);
      if (routeRes.ok) {
        const routeData = await routeRes.json();
        setRoutes(routeData);
      }
    } catch {
      setErrorMsg("Network error during matching check.");
    } finally {
      setLoading(false);
    }
  };

  // Booking seat operations
  const handleBookRide = async (rideId) => {
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const res = await fetch('/api/book-ride', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': user.id
        },
        body: JSON.stringify({ ride_id: rideId })
      });
      const data = await res.json();
      if (res.ok) {
        setSuccessMsg("Booking request submitted! Waiting for driver confirmation.");
        loadBookings();
        loadDriverBookings();
        loadMessages();
        // Re-execute search to update local buttons
        if (searchForm.start && searchForm.end) {
          const searchRes = await fetch(`/api/find-rides?start=${encodeURIComponent(searchForm.start)}&end=${encodeURIComponent(searchForm.end)}`, {
            headers: { 'X-User-Id': user.id }
          });
          const searchData = await searchRes.json();
          if (searchRes.ok) setSearchResults(searchData);
        }
      } else {
        setErrorMsg(data.detail || "Booking failed.");
      }
    } catch {
      setErrorMsg("Network error booking ride.");
    }
  };

  // Driver response (Accept/Reject requests)
  const handleRespondBooking = async (bookingId, action) => {
    setErrorMsg(null);
    try {
      const res = await fetch(`/api/bookings/${bookingId}/respond`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': user.id
        },
        body: JSON.stringify({ action })
      });
      if (res.ok) {
        setSuccessMsg(`Booking successfully ${action === 'ACCEPT' ? 'confirmed' : 'rejected'}.`);
        loadBookings();
        loadDriverBookings();
        loadMessages();
      } else {
        const data = await res.json();
        setErrorMsg(data.detail || "Response update failed.");
      }
    } catch {
      setErrorMsg("Network error updating request status.");
    }
  };

  // Fetch detailed ride view (masks/unmasks phone based on backend authorization checks)
  const handleViewRideDetails = async (rideId) => {
    setErrorMsg(null);
    setSelectedRide(null);
    try {
      const res = await fetch(`/api/ride/${rideId}`, {
        headers: { 'X-User-Id': user.id }
      });
      const data = await res.json();
      if (res.ok) {
        setSelectedRide(data);
        window.location.hash = '#/ride-details';
      } else {
        setErrorMsg(data.detail || "Failed to load ride details.");
      }
    } catch {
      setErrorMsg("Network error loading ride data.");
    }
  };

  // Construct safe waypoint-based navigation link
  const getGoogleMapsDirectionsUrl = (nodes) => {
    if (!nodes || nodes.length < 2) return "";
    const origin = encodeURIComponent(nodes[0] + ", Hyderabad, Telangana, India");
    const dest = encodeURIComponent(nodes[nodes.length - 1] + ", Hyderabad, Telangana, India");
    if (nodes.length > 2) {
      const middle = nodes.slice(1, -1).map(n => n + ", Hyderabad, Telangana, India").join("|");
      return `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${dest}&waypoints=${encodeURIComponent(middle)}&travelmode=driving`;
    }
    return `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${dest}&travelmode=driving`;
  };

  // Sync notifications to localStorage
  useEffect(() => {
    localStorage.setItem('notifications', JSON.stringify(notifications));
  }, [notifications]);

  // Trigger temporary toast and append notification to list
  const triggerToast = (title, message, type = 'info', notifData = null) => {
    const id = Date.now() + Math.random().toString();
    const newToast = { id, title, message, type };
    setToasts(prev => [...prev, newToast]);
    
    // Auto-remove toast after 5 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 5000);

    // Save persistent notification
    const newNotif = {
      id: Date.now() + Math.random().toString(),
      title,
      message,
      type,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      unread: true,
      details: notifData
    };
    setNotifications(prev => [newNotif, ...prev]);
  };

  // Establish WebSocket connection when user logs in
  useEffect(() => {
    if (!user) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws';
    // Use window.location.host since Vite proxies /api to backend
    const wsUrl = `${wsProtocol === 'wss:' ? 'wss:' : 'ws:'}//${window.location.host}/api/ws/${user.id}`;
    
    let socket;
    let reconnectTimeout;

    const connectWebSocket = () => {
      console.log("Connecting to WebSocket:", wsUrl);
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log("WebSocket connected successfully");
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("WebSocket message received:", data);
          
          let toastType = 'info';
          let toastTitle = 'Notification';
          let notifDetails = null;

          if (data.type === 'BOOKING_CONFIRMED') {
            toastType = 'success';
            toastTitle = 'Ride Booked!';
            notifDetails = {
              name: data.contact_name,
              phone: data.contact_phone,
              ride_id: data.ride_id,
              booking_id: data.booking_id
            };
            // Reload user dashboard bookings
            loadBookings();
            loadDriverBookings();
            loadMessages();
            // Reload active ride details if matching the booked ride
            if (window.location.hash === '#/ride-details' && selectedRideRef.current && selectedRideRef.current.ride_id === data.ride_id) {
              handleViewRideDetails(data.ride_id);
            }
          } else if (data.type === 'BOOKING_REJECTED') {
            toastType = 'error';
            toastTitle = 'Booking Rejected';
            loadBookings();
            loadDriverBookings();
            loadMessages();
          } else if (data.type === 'NEW_REQUEST') {
            toastType = 'warning';
            toastTitle = 'New Booking Request';
            loadBookings();
            loadDriverBookings();
            loadMessages();
          } else if (data.type === 'BOOKING_REQUESTED') {
            toastType = 'info';
            toastTitle = 'Request Submitted';
            loadBookings();
            loadDriverBookings();
            loadMessages();
          }

          triggerToast(toastTitle, data.message, toastType, notifDetails);
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };

      socket.onerror = (err) => {
        console.error("WebSocket connection error:", err);
      };

      socket.onclose = (event) => {
        console.log("WebSocket connection closed. Attempting reconnect in 3s...", event.reason);
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      };
    };

    connectWebSocket();

    return () => {
      if (socket) {
        socket.onclose = null;
        socket.close();
      }
      clearTimeout(reconnectTimeout);
    };
  }, [user]);

  return (
    <div className="app-container">
      {/* Header Banner */}
      <header className="app-header">
        <a href="#/" className="logo-container">
          <div className="logo-icon">RB</div>
          <div>
            <h1 className="app-title">RideBuddy</h1>
            <span className="subtitle">Hyderabad Local Office Commute Matcher</span>
          </div>
        </a>

        {/* Global Navigation links */}
        <div className="nav-links">
          {user ? (
            <>
              <a href="#/rider" className={`nav-link ${currentRoute === '#/rider' ? 'active' : ''}`}>Find Ride</a>
              <a href="#/bookings-list" className={`nav-link ${currentRoute === '#/bookings-list' ? 'active' : ''}`}>My Bookings</a>
              <a href="#/driver" className={`nav-link ${currentRoute === '#/driver' ? 'active' : ''}`}>Offer Ride</a>
              <a href="#/bookings-requests" className={`nav-link ${currentRoute === '#/bookings-requests' ? 'active' : ''}`}>Commuter Requests</a>
              <a href="#/messages" className={`nav-link ${currentRoute === '#/messages' ? 'active' : ''}`}>Messages 💬</a>
              {/* Notification Bell Dropdown */}
              <div className="notification-bell-container">
                <button 
                  className="bell-btn" 
                  onClick={() => setShowNotificationsDropdown(!showNotificationsDropdown)}
                  title="Notifications"
                >
                  🔔
                  {notifications.filter(n => n.unread).length > 0 && (
                    <span className="bell-badge">
                      {notifications.filter(n => n.unread).length}
                    </span>
                  )}
                </button>

                {showNotificationsDropdown && (
                  <div className="notification-dropdown">
                    <div className="notification-header">
                      <h3>Notifications</h3>
                      {notifications.length > 0 && (
                        <button className="clear-btn" onClick={() => setNotifications([])}>
                          Clear All
                        </button>
                      )}
                    </div>
                    <div className="notification-list">
                      {notifications.length === 0 ? (
                        <div className="notif-empty">No notifications yet</div>
                      ) : (
                        notifications.map(n => (
                          <div 
                            key={n.id} 
                            className={`notification-item ${n.unread ? 'unread' : ''}`}
                            onClick={() => {
                              // Mark as read
                              setNotifications(prev => prev.map(item => item.id === n.id ? { ...item, unread: false } : item));
                            }}
                          >
                            <div className="toast-icon" style={{ fontSize: '1.1rem' }}>
                              {n.type === 'success' && '✓'}
                              {n.type === 'info' && '🛈'}
                              {n.type === 'warning' && '⏰'}
                              {n.type === 'error' && '⚠️'}
                            </div>
                            <div style={{ flexGrow: 1, textAlign: 'left' }}>
                              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#fff' }}>{n.title}</div>
                              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>{n.message}</div>
                              
                              {n.details && (
                                <div className="notif-details-card">
                                  <div className="notif-details-title">👤 Contact Details</div>
                                  <div className="notif-details-row">
                                    <span>Name:</span>
                                    <strong>{n.details.name}</strong>
                                  </div>
                                  <div className="notif-details-row">
                                    <span>Phone:</span>
                                    <strong>{n.details.phone}</strong>
                                  </div>
                                  <button 
                                    className="btn-primary" 
                                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', marginTop: '0.35rem', width: '100%', boxShadow: 'none' }}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setShowNotificationsDropdown(false);
                                      handleViewRideDetails(n.details.ride_id);
                                    }}
                                  >
                                    View Ride & Map
                                  </button>
                                </div>
                              )}
                              
                              <div className="notif-time">{n.time}</div>
                            </div>
                            <button 
                              className="notification-item-close" 
                              onClick={(e) => {
                                e.stopPropagation();
                                setNotifications(prev => prev.filter(item => item.id !== n.id));
                              }}
                            >
                              &times;
                            </button>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>

              <span className="nav-link" style={{ color: 'var(--text-primary)', cursor: 'default' }}>
                👤 {user.name} ({user.role})
              </span>
              <button className="btn-secondary" onClick={handleLogout} style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}>
                Logout
              </button>
            </>
          ) : (
            <>
              <a href="#/login" className="btn-secondary" style={{ padding: '0.4rem 1rem' }}>Login</a>
              <a href="#/register" className="btn-primary" style={{ padding: '0.4rem 1rem', boxShadow: 'none' }}>Register</a>
            </>
          )}

          <div className={`db-badge ${dbStatus === 'Online' ? '' : 'offline'}`}>
            <div className="db-badge-dot" />
            Graph: {dbStatus}
          </div>
        </div>
      </header>

      {/* Global Alerts feedback */}
      {errorMsg && (
        <div className="alert alert-error">
          <span>⚠️</span>
          <div>{errorMsg}</div>
        </div>
      )}
      {successMsg && (
        <div className="alert alert-success">
          <span>✓</span>
          <div>{successMsg}</div>
        </div>
      )}

      {/* Routing Views switcher */}

      {/* VIEW: Landing page */}
      {currentRoute === '#/' && (
        <div className="landing-hero glass-card" style={{ gap: '2rem' }}>
          <div>
            <h2>Find office carpools in Hyderabad with Graph Traversal</h2>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '700px', margin: '0 auto', fontSize: '1.05rem' }}>
              RideBuddy leverages Neo4j graph technology to dynamically matching office commutes. 
              By checking overlaps on route paths (CONNECTED_TO corridors), we match drivers and riders even when they do not start or end at the exact same location.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center' }}>
            <a href="#/register" className="btn-primary" style={{ padding: '0.9rem 2.5rem', fontSize: '1.1rem' }}>
              Get Started
            </a>
            <a href="#/login" className="btn-secondary" style={{ padding: '0.9rem 2.5rem', fontSize: '1.1rem' }}>
              Sign In
            </a>
          </div>

          <div className="landing-stats" style={{ margin: '0 auto' }}>
            <div className="stat-card">
              <div className="stat-number">30</div>
              <div className="stat-label">Commute Areas</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">400+</div>
              <div className="stat-label">Commuter Accounts</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">200+</div>
              <div className="stat-label">Daily Commutes</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">1,200+</div>
              <div className="stat-label">Graph Connections</div>
            </div>
          </div>
        </div>
      )}

      {/* VIEW: Login */}
      {currentRoute === '#/login' && (
        <div className="auth-container">
          <div className="auth-card">
            <h2 className="card-title" style={{ justifyContent: 'center', marginBottom: '1.5rem' }}>Login to RideBuddy</h2>
            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="form-group">
                <label className="form-label">Phone Number</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="+919876510001"
                  value={loginForm.phone}
                  onChange={(e) => setLoginForm({ ...loginForm, phone: e.target.value })}
                  required 
                />
              </div>
              <div className="form-group">
                <label className="form-label">Password</label>
                <input 
                  type="password" 
                  className="form-input" 
                  placeholder="••••••••"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                  required 
                />
              </div>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? "Authenticating..." : "Login"}
              </button>
            </form>
            <div className="auth-toggle">
              Do not have an account? <a href="#/register">Register here</a>
            </div>
          </div>
        </div>
      )}

      {/* VIEW: Register */}
      {currentRoute === '#/register' && (
        <div className="auth-container">
          <div className="auth-card">
            <h2 className="card-title" style={{ justifyContent: 'center', marginBottom: '1.5rem' }}>Register Account</h2>
            <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="Ramesh Reddy"
                  value={registerForm.name}
                  onChange={(e) => setRegisterForm({ ...registerForm, name: e.target.value })}
                  required 
                />
              </div>
              <div className="form-group">
                <label className="form-label">Phone Number</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="+919876510001"
                  value={registerForm.phone}
                  onChange={(e) => setRegisterForm({ ...registerForm, phone: e.target.value })}
                  required 
                />
              </div>
              <div className="form-group">
                <label className="form-label">Password</label>
                <input 
                  type="password" 
                  className="form-input" 
                  placeholder="••••••••"
                  value={registerForm.password}
                  onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                  required 
                />
              </div>
              <div className="form-group">
                <label className="form-label">Are you commuting or driving?</label>
                <select 
                  className="form-select"
                  value={registerForm.role}
                  onChange={(e) => setRegisterForm({ ...registerForm, role: e.target.value })}
                >
                  <option value="RIDER">Rider (Find rides)</option>
                  <option value="DRIVER">Driver (Offer rides)</option>
                </select>
              </div>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? "Registering..." : "Create Account"}
              </button>
            </form>
            <div className="auth-toggle">
              Already have an account? <a href="#/login">Login here</a>
            </div>
          </div>
        </div>
      )}

      {/* VIEW: Rider Dashboard */}
      {currentRoute === '#/rider' && (
        <div className="main-grid">
          {/* Left search card */}
          <div className="glass-card" style={{ height: 'fit-content' }}>
            <h2 className="card-title">Where are you going?</h2>
            <form onSubmit={handleSearchRides} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="form-group">
                <label className="form-label">Pickup Area</label>
                <select 
                  className="form-select"
                  value={searchForm.start}
                  onChange={(e) => setSearchForm({ ...searchForm, start: e.target.value })}
                  required
                >
                  <option value="">-- Choose Pickup Area --</option>
                  {locations.map(loc => (
                    <option key={`pick-${loc.name}`} value={loc.name}>{loc.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Destination Area</label>
                <select 
                  className="form-select"
                  value={searchForm.end}
                  onChange={(e) => setSearchForm({ ...searchForm, end: e.target.value })}
                  required
                >
                  <option value="">-- Choose Destination --</option>
                  {locations.map(loc => (
                    <option key={`dest-${loc.name}`} value={loc.name}>{loc.name}</option>
                  ))}
                </select>
              </div>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? "Traversing Graph..." : "Search Commute Offers"}
              </button>
            </form>

            {routes.length > 0 && (
              <div style={{ marginTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '1.25rem' }}>
                <h3 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
                  Connected Corridors (CONNECTED_TO*2..4 Hops)
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                  {routes.map((rt, idx) => (
                    <div key={`rt-${idx}`} style={{ fontSize: '0.8rem', background: 'rgba(0,0,0,0.15)', padding: '0.4rem 0.6rem', borderRadius: '4px' }}>
                      {rt.join(" ➔ ")}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right workspace results */}
          <div className="results-workspace">
            {/* SVG Visual Map */}
            <div className="glass-card" style={{ padding: '1rem' }}>
              <h3 className="form-label" style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                Commute Route Visual Map (Hyderabad Coordinate System)
              </h3>
              <InteractiveMap 
                startNode={searchForm.start} 
                endNode={searchForm.end} 
                routePath={null} 
              />
            </div>

            {/* Results Cards List */}
            <div className="glass-card">
              <h2 className="card-title">Matching Shared Rides</h2>
              
              {loading ? (
                <div className="skeleton-loader">
                  <div className="skeleton-item" />
                  <div className="skeleton-item" />
                </div>
              ) : searchResults.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">🚗</div>
                  <h3 style={{ color: '#fff' }}>No Active Commutes Found</h3>
                  <p className="empty-state-text">
                    Enter your pickup and destination in the left sidebar form to check overlapping driver paths.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {searchResults.map((ride) => (
                    <div key={ride.ride_id} className="match-item">
                      <div className="match-header">
                        <div className="driver-info">
                          <div className="driver-avatar" style={{ background: 'rgba(0, 242, 254, 0.1)', color: 'var(--accent-primary)', border: '1px solid rgba(0, 242, 254, 0.25)' }}>
                            {ride.driver_name.charAt(0)}
                          </div>
                          <div className="driver-details">
                            <span className="driver-name">{ride.driver_name}</span>
                            <span className="driver-area">📞 Phone: {ride.driver_phone}</span>
                          </div>
                        </div>
                        <span className="ride-time-badge">{ride.ride_time}</span>
                      </div>

                      <div className="ride-meta">
                        <div className="ride-meta-item">
                          <span>Route: </span>
                          <strong>{ride.ride_start} ➔ {ride.ride_end}</strong>
                        </div>
                        <div className="ride-meta-item">
                          <span>Seats remaining: </span>
                          <strong>{ride.available_seats}</strong>
                        </div>
                      </div>

                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', margin: '0.25rem 0' }}>
                        {ride.route_nodes.map((node, nIdx) => (
                          <span 
                            key={`node-${nIdx}`} 
                            className={`path-node ${node === searchForm.start || node === searchForm.end ? 'highlight' : ''}`}
                          >
                            {node}
                          </span>
                        ))}
                      </div>

                      <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                        <button 
                          className="btn-secondary" 
                          onClick={() => handleViewRideDetails(ride.ride_id)}
                          style={{ flex: 1 }}
                        >
                          View Details & Map
                        </button>
                        
                        {ride.booking_status === "CONFIRMED" ? (
                          <span className="booking-status-badge status-confirmed" style={{ alignSelf: 'center', textAlign: 'center', flex: 1, padding: '0.6rem' }}>
                            ✓ Confirmed
                          </span>
                        ) : ride.booking_status === "PENDING" ? (
                          <span className="booking-status-badge status-pending" style={{ alignSelf: 'center', textAlign: 'center', flex: 1, padding: '0.6rem' }}>
                            ⏰ Waiting for driver
                          </span>
                        ) : ride.booking_status === "REJECTED" ? (
                          <span className="booking-status-badge status-rejected" style={{ alignSelf: 'center', textAlign: 'center', flex: 1, padding: '0.6rem' }}>
                            ⚠️ Rejected
                          </span>
                        ) : (
                          <button 
                            className="btn-primary" 
                            onClick={() => handleBookRide(ride.ride_id)}
                            disabled={ride.available_seats <= 0}
                            style={{ flex: 1 }}
                          >
                            Book Ride
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* VIEW: Rider Bookings List */}
      {currentRoute === '#/bookings-list' && (
        <div className="glass-card">
          <h2 className="card-title">My Booked Rides</h2>
          {bookings.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📋</div>
              <h3>No Bookings Created</h3>
              <p className="empty-state-text">
                You have not booked any shared commutes yet. Head over to the Find Ride page to request seats.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {bookings.map((b) => (
                <div key={b.booking_id} className="match-item">
                  <div className="match-header">
                    <div>
                      <h3 style={{ fontSize: '1.1rem', color: '#fff' }}>Ride with {b.driver_name}</h3>
                      <span className="driver-area">📞 Phone: {b.driver_phone}</span>
                    </div>
                    <span className={`booking-status-badge ${b.booking_status === 'CONFIRMED' ? 'status-confirmed' : b.booking_status === 'PENDING' ? 'status-pending' : 'status-rejected'}`}>
                      {b.booking_status}
                    </span>
                  </div>

                  <div className="ride-meta">
                    <div className="ride-meta-item">
                      <span>Pickup ➔ Destination: </span>
                      <strong>{b.ride_start} ➔ {b.ride_end}</strong>
                    </div>
                    <div className="ride-meta-item">
                      <span>Departure: </span>
                      <strong>{b.ride_time}</strong>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                    <button className="btn-secondary" onClick={() => handleViewRideDetails(b.ride_id)} style={{ flex: 1 }}>
                      View Commute Map
                    </button>
                    {b.booking_status === 'CONFIRMED' && (
                      <a 
                        href={getGoogleMapsDirectionsUrl([b.ride_start, b.ride_end])} 
                        target="_blank" 
                        rel="noreferrer" 
                        className="btn-primary" 
                        style={{ flex: 1, textDecoration: 'none' }}
                      >
                        🧭 Navigate (Google Maps)
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* VIEW: Driver Dashboard */}
      {currentRoute === '#/driver' && (
        <div className="main-grid">
          {/* Offer a Ride form */}
          <div className="glass-card" style={{ height: 'fit-content' }}>
            <h2 className="card-title">Offer a Commute</h2>
            <form onSubmit={handleOfferRide} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="form-group">
                <label className="form-label">Commute Starting Location</label>
                <select 
                  className="form-select"
                  value={rideForm.start}
                  onChange={(e) => setRideForm({ ...rideForm, start: e.target.value })}
                  required
                >
                  <option value="">-- Choose Starting Point --</option>
                  {locations.map(loc => (
                    <option key={`offer-start-${loc.name}`} value={loc.name}>{loc.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Destination Office Area</label>
                <select 
                  className="form-select"
                  value={rideForm.end}
                  onChange={(e) => setRideForm({ ...rideForm, end: e.target.value })}
                  required
                >
                  <option value="">-- Choose Office Destination --</option>
                  {locations.map(loc => (
                    <option key={`offer-end-${loc.name}`} value={loc.name}>{loc.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Departure Time</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. 08:30 AM"
                  value={rideForm.time}
                  onChange={(e) => setRideForm({ ...rideForm, time: e.target.value })}
                  required 
                />
              </div>
              <div className="form-group">
                <label className="form-label">Available Seat Count</label>
                <input 
                  type="number" 
                  className="form-input" 
                  min="1" 
                  max="6"
                  value={rideForm.available_seats}
                  onChange={(e) => setRideForm({ ...rideForm, available_seats: parseInt(e.target.value) })}
                  required 
                />
              </div>
              <button type="submit" className="btn-primary" disabled={loading} style={{ background: 'linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%)', boxShadow: '0 0 15px rgba(124, 58, 237, 0.4)' }}>
                {loading ? "Publishing..." : "Publish Ride Offer"}
              </button>
            </form>
          </div>

          {/* Incoming Bookings requests */}
          <div className="results-workspace">
            {/* SVG Visual Map */}
            <div className="glass-card" style={{ padding: '1rem' }}>
              <h3 className="form-label" style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                Your Offered Commutes Network Map
              </h3>
              <InteractiveMap 
                startNode={rideForm.start} 
                endNode={rideForm.end} 
                routePath={null} 
              />
            </div>

            <div className="glass-card">
              <h2 className="card-title">Manage Commuter Bookings</h2>
              <div style={{ textAlign: 'right', fontSize: '0.85rem' }}>
                <a href="#/bookings-requests" style={{ color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: '600' }}>
                  Open Detailed Request Hub ➔
                </a>
              </div>
              
              {driverBookings.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">📭</div>
                  <h3>No Booking Requests</h3>
                  <p className="empty-state-text">
                    Commuters who request to join your offered commutes will appear here for you to accept/reject.
                  </p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {driverBookings.slice(0, 5).map((b) => (
                    <div key={b.booking_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '0.5rem', border: '1px solid var(--card-border)' }}>
                      <div>
                        <strong style={{ color: '#fff' }}>{b.rider_name}</strong>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                          Route: {b.ride_start} ➔ {b.ride_end} | Time: {b.ride_time}
                        </div>
                      </div>
                      
                      {b.booking_status === "PENDING" ? (
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button className="btn-primary" onClick={() => handleRespondBooking(b.booking_id, 'ACCEPT')} style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', boxShadow: 'none' }}>
                            Accept
                          </button>
                          <button className="btn-danger" onClick={() => handleRespondBooking(b.booking_id, 'REJECT')} style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
                            Reject
                          </button>
                        </div>
                      ) : (
                        <span className={`booking-status-badge ${b.booking_status === 'CONFIRMED' ? 'status-confirmed' : 'status-rejected'}`}>
                          {b.booking_status}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* VIEW: Booking Requests detailed list (Driver) */}
      {currentRoute === '#/bookings-requests' && (
        <div className="glass-card">
          <h2 className="card-title">Commuter Requests Hub</h2>
          {driverBookings.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📋</div>
              <h3>No Incoming Requests</h3>
              <p className="empty-state-text">
                No ride sharing requests have been made for your shared commutes.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {driverBookings.map((b) => (
                <div key={b.booking_id} className="match-item">
                  <div className="match-header">
                    <div>
                      <h3 style={{ fontSize: '1.1rem', color: '#fff' }}>Request from {b.rider_name}</h3>
                      <span className="driver-area">📞 Phone: {b.rider_phone}</span>
                    </div>
                    <span className={`booking-status-badge ${b.booking_status === 'CONFIRMED' ? 'status-confirmed' : b.booking_status === 'PENDING' ? 'status-pending' : 'status-rejected'}`}>
                      {b.booking_status}
                    </span>
                  </div>

                  <div className="ride-meta">
                    <div className="ride-meta-item">
                      <span>Ride offered: </span>
                      <strong>{b.ride_start} ➔ {b.ride_end}</strong>
                    </div>
                    <div className="ride-meta-item">
                      <span>Time: </span>
                      <strong>{b.ride_time}</strong>
                    </div>
                    <div className="ride-meta-item">
                      <span>Seats remaining: </span>
                      <strong>{b.available_seats}</strong>
                    </div>
                  </div>

                  {b.booking_status === "PENDING" && (
                    <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                      <button className="btn-primary" onClick={() => handleRespondBooking(b.booking_id, 'ACCEPT')} style={{ flex: 1 }}>
                        Accept Request & Expose Phone
                      </button>
                      <button className="btn-danger" onClick={() => handleRespondBooking(b.booking_id, 'REJECT')} style={{ flex: 1 }}>
                        Reject Request
                      </button>
                    </div>
                  )}

                  {b.booking_status === "CONFIRMED" && (
                    <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                      <button className="btn-secondary" onClick={() => handleViewRideDetails(b.ride_id)} style={{ flex: 1 }}>
                        View Commute Route Map
                      </button>
                      <a 
                        href={getGoogleMapsDirectionsUrl([b.ride_start, b.ride_end])} 
                        target="_blank" 
                        rel="noreferrer" 
                        className="btn-primary" 
                        style={{ flex: 1, textDecoration: 'none' }}
                      >
                        🧭 View Directions
                      </a>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* VIEW: Messages / SMS Inbox */}
      {currentRoute === '#/messages' && (
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2 className="card-title" style={{ margin: 0 }}>💬 Simulated SMS Inbox</h2>
            <button className="btn-secondary" onClick={loadMessages} style={{ padding: '0.4rem 1rem', fontSize: '0.85rem' }}>
              🔄 Refresh Inbox
            </button>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem', textAlign: 'left' }}>
            Registered Phone: <strong>{user?.phone}</strong>. Showing messages sent to this phone number to link connection.
          </p>

          {smsMessages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">💬</div>
              <h3>No Messages Received</h3>
              <p className="empty-state-text">
                Messages will appear here when you post rides, submit booking requests, or confirm bookings.
              </p>
            </div>
          ) : (
            <div className="sms-list" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {smsMessages.map((msg) => {
                const isFromSystem = msg.from_phone === 'RideBuddy';
                const formattedTime = new Date(msg.timestamp).toLocaleString();
                return (
                  <div key={msg.message_id} className="sms-item" style={{
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid var(--card-border)',
                    borderRadius: '8px',
                    padding: '1rem',
                    textAlign: 'left'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      <span>From: <strong style={{ color: isFromSystem ? 'var(--accent-primary)' : '#fff' }}>{msg.from_phone}</strong></span>
                      <span>To: <strong>{msg.to_phone}</strong></span>
                      <span>{formattedTime}</span>
                    </div>
                    <div className="sms-body" style={{ color: '#fff', fontSize: '0.95rem', lineHeight: '1.4', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '6px' }}>
                      {msg.body}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* VIEW: Ride details with path highlights and map */}
      {currentRoute === '#/ride-details' && selectedRide && (
        <div className="dashboard-grid">
          {/* Left SVG Visual Map */}
          <div className="glass-card">
            <h2 className="card-title">Ride Commute Path Map</h2>
            <InteractiveMap 
              startNode={selectedRide.ride_start} 
              endNode={selectedRide.ride_end} 
              routePath={selectedRide.route_nodes} 
            />
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', background: 'rgba(0,0,0,0.15)', padding: '0.75rem', borderRadius: '6px' }}>
              {selectedRide.route_nodes.map((node, idx) => (
                <React.Fragment key={`path-det-${idx}`}>
                  {idx > 0 && <span style={{ color: 'var(--text-muted)' }}>➔</span>}
                  <span className={`path-node ${node === selectedRide.ride_start ? 'map-node-start' : node === selectedRide.ride_end ? 'map-node-end' : 'highlight'}`} style={{ border: 'none' }}>
                    {node}
                  </span>
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Right ride info details */}
          <div className="glass-card">
            <h2 className="card-title">Commute Details</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="form-group">
                <span className="form-label">Driver Name</span>
                <strong style={{ fontSize: '1.2rem', color: '#fff' }}>{selectedRide.driver_name}</strong>
              </div>

              <div className="form-group">
                <span className="form-label">Driver Contact Number</span>
                {selectedRide.booking_status === "CONFIRMED" || selectedRide.driver_id === user.id ? (
                  <strong style={{ fontSize: '1.1rem', color: 'var(--accent-primary)' }}>
                    {selectedRide.driver_phone}
                  </strong>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <strong style={{ color: 'var(--text-muted)' }}>{selectedRide.driver_phone}</strong>
                    <span style={{ fontSize: '0.75rem', color: 'var(--warning-color)' }}>
                      ⚠️ Phone number is hidden. Confirm booking to expose driver contact details.
                    </span>
                  </div>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <span className="form-label">Departure Time</span>
                  <strong>{selectedRide.ride_time}</strong>
                </div>
                <div className="form-group">
                  <span className="form-label">Remaining Seats</span>
                  <strong>{selectedRide.available_seats}</strong>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <span className="form-label">Start Area</span>
                  <strong>{selectedRide.ride_start}</strong>
                </div>
                <div className="form-group">
                  <span className="form-label">Destination Area</span>
                  <strong>{selectedRide.ride_end}</strong>
                </div>
              </div>

              <div className="form-group">
                <span className="form-label">Booking Status</span>
                {selectedRide.driver_id === user.id ? (
                  <span className="booking-status-badge status-confirmed">Offering Driver</span>
                ) : selectedRide.booking_status ? (
                  <span className={`booking-status-badge ${selectedRide.booking_status === 'CONFIRMED' ? 'status-confirmed' : selectedRide.booking_status === 'PENDING' ? 'status-pending' : 'status-rejected'}`}>
                    {selectedRide.booking_status}
                  </span>
                ) : (
                  <span className="booking-status-badge" style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)' }}>
                    Not Requested
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button 
                  className="btn-secondary" 
                  onClick={() => {
                    window.location.hash = user.role === 'DRIVER' ? '#/driver' : '#/rider';
                  }}
                  style={{ flex: 1 }}
                >
                  Back to Dashboard
                </button>
                
                {selectedRide.booking_status === "CONFIRMED" || selectedRide.driver_id === user.id ? (
                  <a 
                    href={getGoogleMapsDirectionsUrl(selectedRide.route_nodes)} 
                    target="_blank" 
                    rel="noreferrer" 
                    className="btn-primary" 
                    style={{ flex: 1, textDecoration: 'none' }}
                  >
                    🧭 Navigate (Google Maps)
                  </a>
                ) : (
                  !selectedRide.booking_status && (
                    <button 
                      className="btn-primary" 
                      onClick={() => handleBookRide(selectedRide.ride_id)}
                      disabled={selectedRide.available_seats <= 0 || selectedRide.ride_status !== "ACTIVE"}
                      style={{ flex: 1 }}
                    >
                      Book Ride
                    </button>
                  )
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notifications Overlay Container */}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`toast toast-${t.type}`}>
            <div className="toast-icon">
              {t.type === 'success' && '✓'}
              {t.type === 'info' && '🛈'}
              {t.type === 'warning' && '⏰'}
              {t.type === 'error' && '⚠️'}
            </div>
            <div className="toast-content" style={{ textAlign: 'left' }}>
              <div className="toast-title">{t.title}</div>
              <div className="toast-message">{t.message}</div>
            </div>
            <button className="toast-close" onClick={() => setToasts(prev => prev.filter(item => item.id !== t.id))}>
              &times;
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
