import { useState } from 'react';
import {
  Box, Typography, Paper, TextField, Button, Alert, Grid, Chip, Divider,
} from '@mui/material';
import { Lock, Person, EventBusy } from '@mui/icons-material';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function Perfil() {
  const { user, fetchUser } = useAuth();
  const [form, setForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (form.new_password !== form.confirm_password) {
      setError('Las contrasenas nuevas no coinciden.');
      return;
    }
    if (form.new_password.length < 8) {
      setError('La contrasena debe tener al menos 8 caracteres.');
      return;
    }

    setLoading(true);
    try {
      await api.post('/users/users/change_password/', form);
      setSuccess('Contrasena actualizada correctamente.');
      setForm({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cambiar contrasena');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleOOO = async () => {
    try {
      await api.post('/users/users/toggle_out_of_office/');
      await fetchUser();
    } catch (err) {
      alert(err.response?.data?.error || 'Error');
    }
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>Mi Perfil</Typography>

      <Grid container spacing={3}>
        {/* Info del usuario */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <Person />
              <Typography variant="h6">Informacion Personal</Typography>
            </Box>
            <Typography><strong>Nombre:</strong> {user?.first_name} {user?.last_name}</Typography>
            <Typography><strong>Email:</strong> {user?.email}</Typography>
            <Typography><strong>Rol:</strong> {user?.role_display}</Typography>
            <Typography><strong>Area:</strong> {user?.area_name}</Typography>
            <Typography><strong>Ubicacion:</strong> {user?.location_name}</Typography>
            <Typography><strong>Centro de Costos:</strong> {user?.cost_center_name}</Typography>
            {user?.phone && <Typography><strong>Telefono:</strong> {user?.phone}</Typography>}

            <Divider sx={{ my: 2 }} />

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <EventBusy color={user?.is_out_of_office ? 'warning' : 'disabled'} />
              <Typography>
                Fuera de Oficina: {' '}
                <Chip
                  label={user?.is_out_of_office ? 'Activo' : 'Inactivo'}
                  color={user?.is_out_of_office ? 'warning' : 'default'}
                  size="small"
                />
              </Typography>
              <Button variant="outlined" size="small" onClick={handleToggleOOO}>
                {user?.is_out_of_office ? 'Desactivar' : 'Activar'}
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Cambio de contrasena */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <Lock />
              <Typography variant="h6">Cambiar Contrasena</Typography>
            </Box>
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
            <form onSubmit={handleChangePassword}>
              <TextField
                fullWidth label="Contrasena actual" type="password" margin="normal"
                value={form.current_password}
                onChange={(e) => setForm({ ...form, current_password: e.target.value })}
                required
              />
              <TextField
                fullWidth label="Nueva contrasena" type="password" margin="normal"
                value={form.new_password}
                onChange={(e) => setForm({ ...form, new_password: e.target.value })}
                required helperText="Minimo 8 caracteres"
              />
              <TextField
                fullWidth label="Confirmar nueva contrasena" type="password" margin="normal"
                value={form.confirm_password}
                onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
                required
              />
              <Button
                type="submit" variant="contained" fullWidth sx={{ mt: 2 }}
                disabled={loading}
              >
                {loading ? 'Guardando...' : 'Cambiar Contrasena'}
              </Button>
            </form>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
